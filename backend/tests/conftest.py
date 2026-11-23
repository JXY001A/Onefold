"""测试环境固定值。

必须在导入 app 之前生效（pytest 会先加载 conftest）：
环境变量优先级高于 .env 文件，因此这里能压住本地 .env 里的生产配置，
避免测试真发邮件、以及 Secure Cookie 在 http 下不被回传导致身份丢失。
"""

import os

os.environ["ENV"] = "dev"
os.environ["SMTP_HOST"] = ""
os.environ["COOKIE_SECURE"] = "false"