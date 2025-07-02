from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter


from . import views
from .views import (
    receive_dataset_request,
    DatasetViewSet,
    DatasetRequestViewSet,
    DatasetSentViewSet,
    konfirmasi_dataset,           # API view
)

router = DefaultRouter()
router.register(r'datasets', DatasetViewSet)
router.register(r'dataset-request', DatasetRequestViewSet)
router.register(r'dataset-sent', DatasetSentViewSet)

def upload_redirect(request):
    return redirect('upload_step1')

urlpatterns = [
    # Halaman web
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload/", upload_redirect, name="upload_redirect"),
    path("upload/step1/", views.upload_step1, name="upload_step1"),
    path("upload/step2/", views.upload_step2, name="upload_step2"),

    path("mydata/", views.mydata, name="mydata"),
    path("dataset/<int:pk>/", views.dataset_detail, name="dataset_detail"),
    path("edit/<int:pk>/step1/", views.edit_dataset_step1, name="edit_dataset_step1"),
    path("edit/<int:pk>/step2/", views.edit_dataset_step2, name="edit_dataset_step2"),
    path("dataset/<int:pk>/delete/", views.delete_dataset, name="delete_dataset"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    path("dataset/<int:dataset_id>/log_action/", views.log_dataset_action, name="log_dataset_action"),
    path("dataset/<int:dataset_id>/log_print/", views.log_print_action, name="log_print_action"),
    path("dataset/<int:pk>/print/", views.dataset_report, name="print_dataset"),
    path("dataset/<int:pk>/summary-pdf/", views.download_summary_pdf, name="download_summary"),

    # View untuk memilih dataset (HTML)
    path("pilih-dataset/<int:request_id>/", views.pilih_dataset_untuk_request, name="pilih_dataset_untuk_request"),
    path(
        "konfirmasi-pilih-dataset/<int:request_id>/<int:dataset_id>/",
        views.konfirmasi_pilih_dataset,
        name="konfirmasi_pilih_dataset"
    ),

    # View lainnya
    path("request-list/", views.request_list, name="request_list"),
    path("api/dataset-request/", receive_dataset_request),

    # API manual untuk mobile
    path(
        "api/konfirmasi-pilih-dataset/<int:request_id>/<int:dataset_id>/",
        konfirmasi_dataset,
        name="konfirmasi_dataset"
    ),
    path(
        "api/kirim-dataset/<int:dataset_id>/<int:request_id>/",
        views.api_kirim_dataset_ke_teman_file,
        name="api_kirim_dataset_ke_teman"
    ),
    path("api/request-list/", views.api_request_list, name="api_request_list"),

    # path("api/kirim-datasets/", views.kirim_dataset_ke_temann, name="kirim-dataset"),
    

    # Router DRF (pastikan paling bawah)
    path("api/", include(router.urls)),
]
