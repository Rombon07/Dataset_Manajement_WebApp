# dataset/models.py
from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="datasets")
    name = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')  # Tambahan
    cover_image = models.ImageField(upload_to="covers/", null=True, blank=True)
    data_file = models.FileField(upload_to="files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    request_note = models.TextField(blank=True, null=True) 


    def __str__(self):
        return self.name


class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # 'download', 'print', 'api'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.dataset} - {self.action}"



from django.db import models

class DatasetRequest(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True, blank=True)
    nama_model = models.CharField(max_length=100, default="default_model")
    kebutuhan = models.TextField()
    deskripsi = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.nama_model
    


from django.db import models
class DatasetSent(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    dataset_id = models.IntegerField()
    request_id = models.IntegerField()

    name = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete'),
    ], default='new')

    file_url = models.URLField()

    nama_model = models.CharField(max_length=100)
    kebutuhan = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} dikirim untuk {self.nama_model}"
