from tortoise import models, fields


class Zone(models.Model):
    """
    区域:(文，画，扒糖处，灌水区)
    name:区域名
    image:区域的icon图片
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=10)
    image=fields.CharField(max_length=20,default="icon.png")

    class Meta:
        table = "zones"


