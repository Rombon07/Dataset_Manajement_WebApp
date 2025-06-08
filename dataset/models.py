# dataset/models.py
from django.db import models
from django.contrib.auth.models import User


class Dataset(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="datasets")
    name = models.CharField(max_length=100)
    description = models.TextField()
    cover_image = models.ImageField(upload_to="covers/", null=True, blank=True)
    data_file = models.FileField(upload_to="files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # 'download', 'print', 'api'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.dataset} - {self.action}"
