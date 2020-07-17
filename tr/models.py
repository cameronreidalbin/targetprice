from django.db import models

class Package(models.Model):
    name = models.CharField(max_length=200)
    size = models.IntegerField(default=0)
    def getSize(self):
        return self.size
    def __str__(self):
        return self.name + ", " + str(self.size)