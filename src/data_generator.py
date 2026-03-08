"""模拟通知数据生成器 - 移植自AutoGLM项目"""
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import random
import uuid
import json


@dataclass
class MockNotification:
    """模拟通知数据"""
    id: str
    package_name: str
    app_name: str
    title: str
    text: str
    timestamp: int
    category: str  # WECHAT_QQ, WORK_WECHAT, SMS, OTHER

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "packageName": self.package_name,
            "appName": self.app_name,
            "title": self.title,
            "text": self.text,
            "timestamp": self.timestamp,
            "category": self.category
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class NotificationGenerator:
    """通知数据生成器"""

    # 应用配置
    APP_CONFIGS = {
        "WECHAT_QQ": [
            {"package_name": "com.tencent.mm", "app_name": "微信", "senders": ["张三", "李四", "王五", "工作群", "家庭群", "技术交流群"]},
            {"package_name": "com.tencent.mobileqq", "app_name": "QQ", "senders": ["小明", "小红", "同学群", "游戏群"]}
        ],
        "WORK_WECHAT": [
            {"package_name": "com.tencent.wework", "app_name": "企业微信", "senders": ["公司公告", "项目组", "部门群", "周报提醒"]}
        ],
        "SMS": [
            {"package_name": "com.android.messaging", "app_name": "短信", "senders": ["验证码", "物流", "营销", "银行"]}
        ],
        "OTHER": [
            {"package_name": "com.taobao.taobao", "app_name": "淘宝", "senders": ["物流更新", "促销活动"]},
            {"package_name": "com.jingdong.app.mall", "app_name": "京东", "senders": ["订单状态", "优惠券"]},
            {"package_name": "com.sankuai.meituan", "app_name": "美团", "senders": ["外卖状态", "优惠领取"]},
            {"package_name": "com.android.system", "app_name": "系统", "senders": ["存储空间", "系统更新", "安全警告"]}
        ]
    }

    # 消息模板
    MESSAGE_TEMPLATES = {
        "微信": [
            "{sender}: 你好，明天的会议几点开始？",
            "{sender}: 收到，我马上处理",
            "{sender}: [图片]",
            "{sender}: 晚上一起吃饭吗？",
            "{sender}: 文件已发送，请查收",
            "{sender}: 这个问题怎么解决？",
            "{sender}: 周末有空吗？"
        ],
        "QQ": [
            "{sender}: 在吗？",
            "{sender}: 游戏开黑吗？",
            "{sender}: 作业写完了吗？",
            "{sender}: [表情]"
        ],
        "企业微信": [
            "【{sender}】您有一个待审批的申请",
            "【{sender}】会议将于15分钟后开始",
            "【{sender}】本周周报已截止提交",
            "【{sender}】项目进度更新通知",
            "【{sender}】新任务已分配给您"
        ],
        "短信": [
            "【验证码】您的验证码是 {code}，5分钟内有效。",
            "【物流】您的快递已到达{city}转运中心。",
            "【营销】限时优惠！全场5折起，点击查看详情。",
            "【银行】您尾号{account}的账户于{time}支出{amount}元。"
        ],
        "淘宝": [
            "您的包裹正在派送中，预计今日送达",
            "您关注的商品正在降价促销",
            "订单已发货，快递单号: SF{tracking}",
            "您有未使用的优惠券即将过期"
        ],
        "京东": [
            "订单已签收，感谢您的购买",
            "您关注的商品有货了",
            "京东PLUS会员即将到期"
        ],
        "美团": [
            "外卖已送达，祝您用餐愉快",
            "您有新的优惠券可用",
            "商家已接单，正在准备中"
        ],
        "系统": [
            "存储空间不足，请清理不必要的文件",
            "系统更新可用，建议连接WiFi后下载",
            "检测到异常登录，请确认是否为本人操作",
            "电池电量低，请及时充电"
        ]
    }

    def __init__(self, distribution: dict = None):
        """初始化

        Args:
            distribution: 通知分布配置，如 {"WECHAT_QQ": 30, "WORK_WECHAT": 20, "SMS": 30, "OTHER": 20}
        """
        self.distribution = distribution or {
            "WECHAT_QQ": 30,
            "WORK_WECHAT": 20,
            "SMS": 30,
            "OTHER": 20
        }

    def generate(self, count: int = 100) -> List[MockNotification]:
        """生成模拟通知数据

        Args:
            count: 通知总数

        Returns:
            通知列表
        """
        notifications = []
        now = datetime.now()

        for category, percentage in self.distribution.items():
            category_count = int(count * percentage / 100)
            notifications.extend(
                self._generate_for_category(category, category_count, now)
            )

        # 按时间戳排序
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)

    def _generate_for_category(
        self, category: str, count: int, base_time: datetime
    ) -> List[MockNotification]:
        """为特定类别生成通知"""
        configs = self.APP_CONFIGS.get(category, [])
        if not configs:
            return []

        notifications = []
        for _ in range(count):
            app_config = random.choice(configs)
            sender = random.choice(app_config["senders"])
            templates = self.MESSAGE_TEMPLATES.get(app_config["app_name"], ["来自{app_name}的通知"])
            template = random.choice(templates)

            # 替换模板中的占位符
            message = template.replace("{sender}", sender)
            if "{code}" in message:
                message = message.replace("{code}", str(random.randint(100000, 999999)))
            if "{city}" in message:
                message = message.replace("{city}", random.choice(["北京", "上海", "广州", "深圳"]))
            if "{account}" in message:
                message = message.replace("{account}", str(random.randint(1000, 9999)))
            if "{time}" in message:
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                message = message.replace("{time}", f"{hour}:{minute:02d}")
            if "{amount}" in message:
                message = message.replace("{amount}", str(random.randint(100, 999)))
            if "{tracking}" in message:
                message = message.replace("{tracking}", str(random.randint(100000000, 999999999)))

            notifications.append(MockNotification(
                id=str(uuid.uuid4()),
                package_name=app_config["package_name"],
                app_name=app_config["app_name"],
                title=sender if category != "SMS" and category != "OTHER" else app_config["app_name"],
                text=message,
                timestamp=int((base_time - timedelta(seconds=random.randint(0, 86400))).timestamp() * 1000),
                category=category
            ))

        return notifications

    def to_json_string(self, notifications: List[MockNotification]) -> str:
        """将通知列表转换为JSON字符串"""
        return json.dumps(
            [n.to_dict() for n in notifications],
            ensure_ascii=False,
            indent=2
        )
