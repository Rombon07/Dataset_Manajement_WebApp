from rest_framework import serializers
from .models import Dataset

# class DatasetRequestSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Dataset
#         fields = ['name', 'description', 'status', 'request_note']

from rest_framework import serializers
from .models import DatasetRequest

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = '__all__'

        
class DatasetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetRequest
        fields = '__all__'




from .models import DatasetSent

class DatasetSentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetSent
        fields = '__all__'
