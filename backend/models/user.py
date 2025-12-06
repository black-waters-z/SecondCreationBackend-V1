from tortoise import models, fields


class User(models.Model):
    """
        这是一个使用用户user的tortoise模型
        ID为自动生成的主键，
        用户名长度在20以内，
        密码使用hash编码,
        email:用户邮箱，用来激活用户
        avatar:用户头像（保存在静态文件中，使用https:xxx.xxx.xxx:80/(随机数).png，生成不会重复的png图片，默认为fish.png
        activated:是否激活：可以自由发帖访问
        是否禁言:true禁言，false不禁言
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=20, unique=True)
    password_hash = fields.CharField(max_length=128, null=True)
    email = fields.CharField(max_length=20)
    avatar = fields.CharField(default="avatar1.PNG", max_length=100)  # url地址的后缀，可以为avatar.png
    activated = fields.BooleanField(default=False)
    silence = fields.BooleanField(default=False)

    following = fields.ManyToManyField(
        "models.User",
        related_name="followers",
        through="user_follows",
        forward_key="following_id",  # 当前用户是被关注者
        backward_key="follower_id"  # 关联的用户是关注者
        # 保持这个配置永远不变
    )

    class Meta:
        table = "users"
