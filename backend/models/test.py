from enum import Enum

from tortoise import fields
from tortoise.fields import CASCADE, SET_NULL
from tortoise.models import Model

# #
# class TestModel(Model):
#     id = fields.IntField(pk=True)
#     name_id = fields.ManyToManyField("models.AA", related_name="tag_test")
# #
#
# class AA(Model):
#     id = fields.IntField(pk=True)
#     name = fields.CharField(max_length=100)
