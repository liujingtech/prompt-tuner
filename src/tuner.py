"""提示词调优主控制器"""
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

from src.config import Config, ModelConfig
from src.client import ZhipuClient, ModelResponse
from src.parser import OutputParser, ParsedOutput
from src.scorer import OutputScorer, ScoringResult
from src.optimizer import PromptOptimizer
from src.reporter import Reporter
from src.data_generator import NotificationGenerator, MockNotification


class PromptTuner:
    """提示词调优主控制器"""

    # 初始提示词（用户提供）
    INITIAL_SYSTEM_PROMPT = """【最重要规则】你的输出必须完整包含这3对标签：
1. 【思考】...【思考】- 必须闭合
2. 【TTS】...【TTS】- 必须闭合
3. <show>...</show> - 必须闭合，注意这里是两个标签：<show>开始，</show>结束

如果缺少任何一个闭合标签，输出将被视为无效！

【输出格式 - 必须严格遵守】
【思考】{分级筛选逻辑，不超过30字}【思考】
【TTS】{语音播报内容}【TTS】
<show>
{屏幕显示内容}
</show>

【输出示例】
【思考】筛选一级工作财务通知合并去重【思考】
【TTS】您有两条待审批通知一条银行支出【TTS】
<show>一级通知
企业微信 待审批两条
银行 支出四百一十三元

二级通知
微信 消息三条
美团 外卖已送达

三级通知
营销类 优惠两条</show>

【重要说明】
1. 必须完全按照上面的格式和示例输出
2. 思考内容不超过30字
3. TTS内容不超过15句，每句不超过30字
4. SHOW内容按优先级排列，单条不超过20字

【分级规则】

一级（必须TTS全量播报，SHOW置顶展示）：
- 工作类：企业微信待审批、会议提醒、工作任务分配、截止类工作通知
- 财务类：银行账户变动、收付款、还款提醒
- 安全类：账号异常登录、安全警告、车辆违章提醒

二级（TTS仅汇总核心条数，不播报详情，SHOW二级位置展示）：
- 社交类：微信/QQ个人私信、家人群等重要群聊消息
- 生活类：外卖、快递、取件码、水电煤缴费通知
- 出行类：行程、停车、限行、导航相关通知

三级（仅SHOW末尾展示，绝对禁止TTS播报）：
- 营销类：促销、优惠、广告、活动、优惠券推送
- 娱乐类：音乐、视频、游戏、热点、非重要群聊消息
- 系统类：非紧急系统提醒、存储提醒、应用更新、验证码短信
- 其他无明确优先级的低重要度通知

【TTS语音播报强制约束】
1. 仅可播报一级通知核心内容+二级通知条数汇总，禁止播报三级任何内容
2. 口语化、简洁自然，无任何特殊符号、标点
3. 总句数不超过15句，单句不超过30个字
4. 无一级/二级重要通知时，仅输出：暂无重要通知

【SHOW屏幕展示强制约束】
1. 严格按「一级>二级>三级」优先级排序，同级别按应用分类展示
2. 同类重复通知必须合并去重，仅保留1条，禁止重复展示
3. 单条内容精简，不超过20个字，禁止长文本
4. 禁止编造、新增任何通知中不存在的信息
5. 纯文本分条展示，禁止使用markdown、表情、特殊符号

【绝对禁止行为】
违反任意一条均为无效输出：
1. 禁止输出标签格式外的任何文字、解释、统计、说明内容
2. 禁止修改、增减、拆分标签结构
3. 禁止使用任何markdown格式、表情、特殊符号
4. 禁止编造通知数据、统计数字、不存在的内容
5. 禁止突破分级规则播报、展示内容"""

    INITIAL_USER_PROMPT_TEMPLATE = """以下是需要处理的通知数据：
{notifications}"""

    def __init__(self, config: Config):
        self.config = config
        self.reporter = Reporter(config.output_dir)
        self.generator = NotificationGenerator()

        # 初始化提示词
        self.system_prompt = self.INITIAL_SYSTEM_PROMPT
        self.user_prompt_template = self.INITIAL_USER_PROMPT_TEMPLATE

        # 结果存储
        self.results_by_model: Dict[str, List[Dict]] = {}
        self.best_result: Optional[Dict[str, Any]] = None

        # 计数器
        self.total_iterations = 0
        self.start_time: Optional[float] = None

    def run(self):
        """运行调优过程"""
        self.start_time = time.time()
        max_time = self.config.scoring.max_runtime_hours * 3600

        print(f"\n{'='*60}")
        print(f"提示词调优工具启动")
        print(f"{'='*60}")
        print(f"配置: {len(self.config.models)} 个模型")
        print(f"收敛阈值: 总分 >= {self.config.scoring.total_score}, 各维度 >= {self.config.scoring.dimension_score}")
        print(f"最大迭代: {self.config.scoring.max_iterations} 次/模型")
        print(f"最大运行时间: {self.config.scoring.max_runtime_hours} 小时")
        print(f"{'='*60}\n")

        # 生成测试数据
        notifications = self.generator.generate(100)
        notifications_json = self.generator.to_json_string(notifications)
        print(f"生成了 {len(notifications)} 条测试通知\n")

        for model_config in self.config.models:
            print(f"\n{'-'*60}")
            print(f"测试模型: {model_config.name}")
            print(f"{'-'*60}")

            model_result = self._test_model(
                model_config,
                notifications,
                notifications_json,
                max_time
            )

            if model_result:
                self.results_by_model[model_config.name] = model_result

                # 更新最佳结果
                best_score = max(r['score'] for r in model_result)
                if self.best_result is None or best_score > self.best_result.get('score', 0):
                    self.best_result = {
                        'model': model_config.name,
                        'score': best_score,
                        'system_prompt': self.system_prompt,
                        'user_prompt_template': self.user_prompt_template,
                        'optimization_history': []
                    }

            # 检查时间限制
            if time.time() - self.start_time > max_time:
                print("\n⏰ 达到最大运行时间")
                break

        # 生成最终报告
        self._generate_final_report()

    def _test_model(
        self,
        model_config: ModelConfig,
        notifications: List[MockNotification],
        notifications_json: str,
        max_time: float
    ) -> Optional[List[Dict]]:
        """测试单个模型"""
        client = ZhipuClient(model_config)
        optimizer = PromptOptimizer(self.system_prompt, self.user_prompt_template)
        scorer = OutputScorer()

        results = []
        consecutive_passes = 0

        for iteration in range(self.config.scoring.max_iterations):
            self.total_iterations += 1

            # 检查时间限制
            if time.time() - self.start_time > max_time:
                break

            # 构建用户提示词
            user_prompt = self.user_prompt_template.replace("{notifications}", notifications_json)

            # 调用模型
            print(f"  [{iteration+1}] 调用 {model_config.name}...", end=" ", flush=True)
            response = client.chat(
                system_prompt=optimizer.system_prompt,
                user_prompt=user_prompt,
                stream=False
            )

            if not response.success:
                print(f"✗ API错误: {response.error}")
                time.sleep(2)
                continue

            # 解析输出
            parsed = OutputParser.parse(response.content)

            # 评分
            score_result = scorer.score(parsed, notifications)

            print(f"分数: {score_result.total_score:.1f}/100 - {'✓' if score_result.passed else '✗'}")

            # 保存结果
            result = {
                'iteration': iteration + 1,
                'score': score_result.total_score,
                'passed': score_result.passed,
                'response_time': response.total_time,
                'raw_output': response.content[:500]
            }
            results.append(result)

            # 保存详细结果
            self.reporter.save_iteration_result(
                model_name=model_config.name,
                iteration=iteration + 1,
                system_prompt=optimizer.system_prompt,
                user_prompt=user_prompt,
                raw_output=response.content,
                parsed=parsed,
                score=score_result,
                notifications_count=len(notifications),
                response_time=response.total_time or 0.0
            )

            # 检查收敛（仅记录，不提前退出）
            if score_result.passed:
                consecutive_passes += 1
            else:
                consecutive_passes = 0

                # 优化提示词
                if score_result.total_score < self.config.scoring.total_score:
                    optimizer.optimize(score_result)
                    print(f"    → 优化提示词")

            time.sleep(1)  # 避免请求过快

        return results

    def _check_convergence(self) -> bool:
        """检查是否达到收敛条件"""
        if not self.best_result:
            return False

        # 检查是否有模型连续通过足够次数
        for model_name, results in self.results_by_model.items():
            if len(results) >= self.config.scoring.consecutive_passes:
                recent = results[-self.config.scoring.consecutive_passes:]
                if all(r['passed'] for r in recent):
                    return True

        return False

    def _generate_final_report(self):
        """生成最终报告"""
        total_time = time.time() - self.start_time if self.start_time else 0

        report = self.reporter.generate_final_report(
            best_result=self.best_result or {},
            total_iterations=self.total_iterations,
            total_time_seconds=total_time,
            model_results=self.results_by_model
        )

        print(f"\n{'='*60}")
        print("调优完成！")
        print(f"{'='*60}")
        print(f"总迭代: {self.total_iterations}")
        print(f"总时间: {total_time/60:.1f} 分钟")
        if self.best_result:
            print(f"最佳分数: {self.best_result['score']:.1f}/100")
            print(f"最佳模型: {self.best_result['model']}")
        print(f"\n报告已保存到: {self.config.output_dir}/")
