# Built-in Django
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseNotFound
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils.dateparse import parse_date

# Third-party
import matplotlib

matplotlib.use("Agg")
import pandas as pd
import os
import base64
import io
import matplotlib.pyplot as plt
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.offline import plot
from xhtml2pdf import pisa
from django.core.files.base import ContentFile

# cetak dokumen
from django.shortcuts import render, get_object_or_404
from .models import Dataset
import pandas as pd
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from xhtml2pdf import pisa
import pandas as pd
import matplotlib.pyplot as plt
import io, base64

# Local imports
from .models import Dataset, DownloadLog
from .forms import DatasetInfoForm, DatasetFileForm

from io import BytesIO

#upload
from .forms import DatasetInfoForm, DatasetFileForm
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from PIL import Image
import sys
from django.contrib import messages


#edit
from django.shortcuts import render, get_object_or_404, redirect
from .models import Dataset
from .forms import DatasetInfoForm, DatasetFileForm
import base64
from django.core.files.base import ContentFile


#api
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import DatasetRequestSerializer


@login_required
def dashboard(request):
    datasets = Dataset.objects.all().order_by("-uploaded_at")
    query = request.GET.get("q", "")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if query:
        datasets = datasets.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(data_file__icontains=query)
            | Q(uploaded_at__icontains=query)
        )
    if start_date:
        datasets = datasets.filter(uploaded_at__date__gte=parse_date(start_date))
    if end_date:
        datasets = datasets.filter(uploaded_at__date__lte=parse_date(end_date))

    return render(
        request,
        "dataset/dashboard.html",
        {
            "datasets": datasets,
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@login_required
# def upload_dataset(request):
#     if request.method == "POST":
#         if "captured_image" in request.POST and request.POST["captured_image"]:
#             captured_image = request.POST["captured_image"]
#             format, imgstr = captured_image.split(";base64,")
#             ext = format.split("/")[-1]
#             file_data = ContentFile(
#                 base64.b64decode(imgstr), name=f"camera_capture.{ext}"
#             )
#             request.FILES["cover_image"] = file_data

#         form = DatasetForm(request.POST, request.FILES)
#         if form.is_valid():
#             dataset = form.save(commit=False)
#             dataset.owner = request.user
#             dataset.save()
#             return redirect("dashboard")
#     else:
#         form = DatasetForm()
#     return render(request, "dataset/upload.html", {"form": form})

@login_required
def upload_step1(request):
    if request.method == "POST":
        form = DatasetInfoForm(request.POST)
        if form.is_valid():
            # Simpan data bersih ke session
            request.session["dataset_info"] = {
                "name": form.cleaned_data["name"],
                "description": form.cleaned_data["description"],
                "status": form.cleaned_data["status"],
            }
            return redirect("upload_step2")
    else:
        form = DatasetInfoForm()
    return render(request, "dataset/upload_step1.html", {"form": form})


@login_required
def upload_step2(request):
    if "dataset_info" not in request.session:
        return redirect("upload_step1")

    if request.method == "POST":
        # Salin file upload
        files = request.FILES.copy()

        form = DatasetFileForm(request.POST, files)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.name = request.session["dataset_info"]["name"]
            dataset.description = request.session["dataset_info"]["description"]
            dataset.owner = request.user

            # Tangani gambar dari kamera
            captured_image = request.POST.get("captured_image")
            if captured_image:
                format, imgstr = captured_image.split(";base64,")
                ext = format.split("/")[-1]
                file_data = ContentFile(base64.b64decode(imgstr), name=f"camera_capture.{ext}")
                dataset.cover_image = file_data  # <- secara eksplisit ditetapkan

            dataset.save()
            del request.session["dataset_info"]
            return redirect("dashboard")
        else:
            messages.error(request, "Upload gagal. Periksa kembali file yang diunggah.")
    else:
        form = DatasetFileForm()

    return render(request, "dataset/upload_step2.html", {"form": form})



@login_required
def mydata(request):
    datasets = Dataset.objects.filter(owner=request.user)
    query = request.GET.get("q", "")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if query:
        datasets = datasets.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(data_file__icontains=query)
            | Q(uploaded_at__icontains=query)
        )
    if start_date:
        datasets = datasets.filter(uploaded_at__date__gte=parse_date(start_date))
    if end_date:
        datasets = datasets.filter(uploaded_at__date__lte=parse_date(end_date))

    return render(
        request,
        "dataset/mydata.html",
        {
            "datasets": datasets,
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


@login_required
@require_POST
def log_dataset_action(request, dataset_id):
    action = request.POST.get("action")
    dataset = get_object_or_404(Dataset, id=dataset_id)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action=action)
    return JsonResponse({"status": "success"})




# 
# dataset detail lama grafic pyplot
# @login_required
# def dataset_detail(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     DownloadLog.objects.create(user=request.user, dataset=dataset, action="view_detail")

#     preview_html, bar_plot_html, box_plot_html = None, None, None

#     try:
#         if dataset.data_file and os.path.exists(dataset.data_file.path):
#             df = pd.read_csv(dataset.data_file.path, nrows=10)
#             preview_html = df.to_html(
#                 classes=["table", "table-striped", "table-bordered", "text-center"]
#             )
#             numeric_cols = df.select_dtypes(include="number").columns.tolist()

#             if numeric_cols:
#                 fig_bar = px.bar(
#                     df,
#                     x=df.index,
#                     y=numeric_cols[0],
#                     title=f"Bar Chart - {numeric_cols[0]}",
#                 )
#                 bar_plot_html = plot(fig_bar, output_type="div")

#                 fig_box = go.Figure()
#                 for col in numeric_cols:
#                     fig_box.add_trace(go.Box(y=df[col], name=col))
#                 fig_box.update_layout(title="Boxplot Data Numerik")
#                 box_plot_html = plot(fig_box, output_type="div")
#     except Exception as e:
#         preview_html = f"<p class='text-danger'>Gagal memuat file: {str(e)}</p>"

#     logs = (
#         DownloadLog.objects.filter(dataset=dataset)
#         .select_related("user")
#         .order_by("-timestamp")
#     )
#     return render(
#         request,
#         "dataset/dataset_detail.html",
#         {
#             "dataset": dataset,
#             "preview": preview_html,
#             "bar_plot": bar_plot_html,
#             "box_plot": box_plot_html,
#             "logs": logs,
#         },
#     )

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
import pandas as pd
import os
import io
import base64
import matplotlib.pyplot as plt
from .models import Dataset, DownloadLog

@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action="view_detail")

    preview_html, chart_base64, boxplot_base64 = None, None, None

    try:
        if dataset.data_file and os.path.exists(dataset.data_file.path):
            file_path = dataset.data_file.path
            if file_path.endswith(".csv"):
                df_preview = pd.read_csv(file_path, nrows=10)
                df_chart = pd.read_csv(file_path, nrows=100)
            elif file_path.endswith(".xlsx"):
                df_preview = pd.read_excel(file_path, nrows=10)
                df_chart = pd.read_excel(file_path, nrows=100)
            else:
                df_preview = df_chart = pd.DataFrame()

            preview_html = df_preview.to_html(
                classes=["table", "table-striped", "table-bordered", "text-center"]
            )

            numeric_df = df_chart.select_dtypes(include="number")

            if not numeric_df.empty:
                # Bar chart
                fig, ax = plt.subplots(figsize=(6,4))
                numeric_df.plot(kind="bar", ax=ax)
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format="png", dpi=72)
                buf.seek(0)
                chart_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode()
                plt.close(fig)

                # Boxplot
                fig2, ax2 = plt.subplots(figsize=(6,4))
                numeric_df.plot(kind="box", ax=ax2)
                plt.tight_layout()
                buf2 = io.BytesIO()
                plt.savefig(buf2, format="png", dpi=72)
                buf2.seek(0)
                boxplot_base64 = "data:image/png;base64," + base64.b64encode(buf2.read()).decode()
                plt.close(fig2)
    except Exception as e:
        preview_html = f"<p class='text-danger'>Gagal memuat file: {str(e)}</p>"

    logs = DownloadLog.objects.filter(dataset=dataset).order_by("-timestamp")

    return render(request, "dataset/dataset_detail.html", {
        "dataset": dataset,
        "preview": preview_html,
        "chart_base64": chart_base64,
        "boxplot_base64": boxplot_base64,
        "logs": logs
    })




@login_required
# def edit_dataset(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
#     if request.method == "POST":
#         form = DatasetForm(request.POST, request.FILES, instance=dataset)
#         if form.is_valid():
#             updated_dataset = form.save(commit=False)
#             captured_image = request.POST.get("captured_image")
#             if captured_image:
#                 format, imgstr = captured_image.split(";base64,")
#                 ext = format.split("/")[-1]
#                 file_name = f"captured_image.{ext}"
#                 updated_dataset.cover_image = ContentFile(
#                     base64.b64decode(imgstr), name=file_name
#                 )
#             updated_dataset.save()
#             return redirect("mydata")
#     else:
#         form = DatasetForm(instance=dataset)
#     return render(request, "dataset/edit.html", {"form": form, "dataset": dataset})
# views.py
@login_required
def edit_dataset_step1(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)

    if request.method == 'POST':
        form = DatasetInfoForm(request.POST, instance=dataset)
        if form.is_valid():
            form.save()
            return redirect('edit_dataset_step2', pk=dataset.pk)
    else:
        form = DatasetInfoForm(instance=dataset)

    return render(request, 'dataset/edit_step1.html', {
        'form': form,
        'dataset': dataset
    })


@login_required
def edit_dataset_step2(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)

    if request.method == 'POST':
        form = DatasetFileForm(request.POST, request.FILES, instance=dataset)

        # Tangani foto dari kamera (captured_image)
        captured_image_data = request.POST.get('captured_image')
        if captured_image_data:
            format, imgstr = captured_image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_file = ContentFile(base64.b64decode(imgstr), name=f'captured_{dataset.pk}.{ext}')
            dataset.cover_image = image_file

        if form.is_valid():
            form.save()
            return redirect('mydata')  # Ganti sesuai nama halaman tujuan setelah edit
    else:
        form = DatasetFileForm(instance=dataset)

    return render(request, 'dataset/edit_step2.html', {
        'form': form,
        'dataset': dataset
    })



@login_required
def delete_dataset(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, owner=request.user)
    dataset.delete()
    return redirect("mydata")


@login_required
def download_dataset(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action="download")
    return FileResponse(dataset.data_file.open("rb"), as_attachment=True)


@login_required
def dataset_report(request, pk, as_pdf=False):
    dataset = get_object_or_404(Dataset, pk=pk)

    file_path = dataset.data_file.path
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame()

    preview_html = df.head(10).to_html(classes="table table-bordered", index=False)

    chart_base64 = boxplot_base64 = None
    numeric_df = df.select_dtypes(include="number").head(10)

    if not numeric_df.empty:
        # Bar Chart
        fig, ax = plt.subplots(figsize=(6, 4))
        numeric_df.plot(kind="bar", ax=ax)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        chart_base64 = "data:image/png;base64," + base64.b64encode(buf.read()).decode()
        plt.close()

        # Boxplot
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        numeric_df.plot(kind="box", ax=ax2)
        plt.tight_layout()
        buf2 = io.BytesIO()
        plt.savefig(buf2, format="png")
        buf2.seek(0)
        boxplot_base64 = "data:image/png;base64," + base64.b64encode(buf2.read()).decode()
        plt.close()

    logs = DownloadLog.objects.filter(dataset=dataset).order_by("-timestamp")

    context = {
        "dataset": dataset,
        "preview": preview_html,
        "chart_base64": chart_base64,
        "boxplot_base64": boxplot_base64,
        "logs": logs,
        "user": request.user,
    }

    if as_pdf:
        DownloadLog.objects.create(user=request.user, dataset=dataset, action="download_summary")
        html_string = render_to_string("dataset/summary_pdf.html", context)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{dataset.name}_summary.pdf"'
        pisa_status = pisa.CreatePDF(src=html_string, dest=response)
        if pisa_status.err:
            return HttpResponse("Terjadi kesalahan saat membuat PDF", status=500)
        return response
    else:
        DownloadLog.objects.create(user=request.user, dataset=dataset, action="print")
        return render(request, "dataset/print_dataset.html", context)


def download_summary_pdf(request, pk):
    return dataset_report(request, pk, as_pdf=True)


@login_required
def log_print_action(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action="print")
    return JsonResponse({"status": "ok"})


from .models import Dataset, DatasetRequest


def request_list(request):
    datasets = DatasetRequest.objects.select_related('dataset').all().order_by('-timestamp')
    return render(request, 'dataset/request_list.html', {'datasets': datasets})



def test_404(request):
    return render(request, "404.html", status=404)


def pilih_dataset_untuk_request(request, request_id):
    req = get_object_or_404(DatasetRequest, id=request_id)
    datasets = Dataset.objects.filter(owner=request.user)

    return render(request, 'dataset/pilih_dataset.html', {
        'request_obj': req,
        'datasets': datasets
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def konfirmasi_pilih_dataset(request, request_id, dataset_id):
    dataset_request = get_object_or_404(DatasetRequest, id=request_id)
    dataset = get_object_or_404(Dataset, id=dataset_id, owner=request.user)

    # Kaitkan dataset ke permintaan
    dataset_request.dataset = dataset
    dataset_request.save()

    messages.success(request, "Dataset berhasil dikaitkan dengan permintaan.")
    return redirect("request_list")  # Pastikan ini adalah nama URL yang benar


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import DatasetRequestSerializer

@api_view(['POST'])
def receive_dataset_request(request):
    serializer = DatasetRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# dataset/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Dataset, DatasetRequest
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@csrf_exempt
# @login_required
def api_kirim_dataset_ke_teman(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            dataset_id = data.get("dataset_id")
            request_id = data.get("request_id")

            if not dataset_id or not request_id:
                return JsonResponse({"success": False, "message": "Dataset ID dan Request ID wajib diisi."}, status=400)

            # Validasi dataset
            try:
                dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
            except Dataset.DoesNotExist:
                return JsonResponse({"success": False, "message": "Dataset tidak ditemukan atau bukan milik Anda."}, status=403)

            # Validasi request
            try:
                request_obj = DatasetRequest.objects.get(id=request_id)
            except DatasetRequest.DoesNotExist:
                return JsonResponse({"success": False, "message": "Permintaan dataset tidak ditemukan."}, status=404)

            # Update permintaan agar terkait ke dataset yang dipilih
            request_obj.dataset = dataset
            request_obj.save()

            return JsonResponse({"success": True, "message": "Dataset berhasil dikirim ke teman."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Format data tidak valid."}, status=400)
    
    return JsonResponse({"success": False, "message": "Hanya menerima metode POST."}, status=405)


import requests
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Dataset, DatasetRequest
from .models import DatasetSent



# @login_required
# def api_kirim_dataset_ke_teman_url(request, dataset_id, request_id):
#     if request.method == "GET":
#         try:
#             # Validasi dataset milik user
#             dataset = Dataset.objects.get(id=dataset_id, owner=request.user)
#         except Dataset.DoesNotExist:
#             return JsonResponse({"success": False, "message": "Dataset tidak ditemukan atau bukan milik Anda."}, status=403)

#         try:
#             # Validasi request
#             dataset_request = DatasetRequest.objects.get(id=request_id)
#         except DatasetRequest.DoesNotExist:
#             return JsonResponse({"success": False, "message": "Permintaan tidak ditemukan."}, status=404)

#         # Update permintaan agar terkait ke dataset
#         dataset_request.dataset = dataset
#         dataset_request.save()

#         # Payload JSON yang akan dikirim ke teman
#         payload = {
#             "dataset_id": dataset.id,
#             "request_id": dataset_request.id,
#             "name": dataset.name,
#             "description": dataset.description,
#             "status": dataset.status,
#             "data_file_url": request.build_absolute_uri(dataset.data_file.url),
#             "nama_model": dataset_request.nama_model,
#             "kebutuhan": dataset_request.kebutuhan,
#         }

#         try:
#             # Kirim ke endpoint teman via jaringan VLAN
#             response = requests.post(
#                 "http://10.24.64.10:8000/api/terima-dataset/",
#                 json=payload,
#                 timeout=5
#             )

#             if response.status_code == 200:
#                 # Simpan ke DatasetSent hanya jika berhasil
#                 DatasetSent.objects.create(
#                     sender=request.user,
#                     dataset_id=dataset.id,
#                     request_id=dataset_request.id,
#                     name=dataset.name,
#                     description=dataset.description,
#                     status=dataset.status,
#                     file_url=payload["data_file_url"],
#                     nama_model=dataset_request.nama_model,
#                     kebutuhan=dataset_request.kebutuhan,
#                 )

#                 return JsonResponse({"success": True, "message": "Dataset berhasil dikirim ke teman."})

#             return JsonResponse({"success": False, "message": f"Gagal kirim ke teman: {response.status_code}"})

#         except requests.exceptions.RequestException as e:
#             return JsonResponse({"success": False, "message": f"Gagal terhubung ke teman: {e}"})

#     return JsonResponse({"success": False, "message": "Metode tidak diperbolehkan."}, status=405)

import requests
@csrf_exempt
# @login_required
def api_kirim_dataset_ke_teman_file(request, dataset_id, request_id):
    if request.method == "POST":
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            return JsonResponse({"success": False, "message": "Dataset tidak ditemukan atau bukan milik Anda."}, status=403)

        try:
            dataset_request = DatasetRequest.objects.get(id=request_id)
        except DatasetRequest.DoesNotExist:
            return JsonResponse({"success": False, "message": "Permintaan tidak ditemukan."}, status=404)

        dataset_request.dataset = dataset
        dataset_request.save()

        # Buka file CSV yang akan dikirim
        file_path = dataset.data_file.path
        with open(file_path, 'rb') as f:
            files = {
                'file': (dataset.data_file.name, f, 'text/csv'),
            }
            data = {
                'dataset_id': dataset.id,
                'request_id': dataset_request.id,
                'name': dataset.name,
                'description': dataset.description,
                'status': dataset.status,
                'nama_model': dataset_request.nama_model,
                'kebutuhan': dataset_request.kebutuhan,
            }

            try:
                response = requests.post(
                    "http://10.40.28.91:8000/api/terima-dataset/",
                    files=files,
                    data=data,
                    timeout=10
                )

                if response.status_code == 200:
                    return JsonResponse({"success": True, "message": "Dataset berhasil dikirim (dengan file)."})
                else:
                    return JsonResponse({"success": True, "message": f"Dataset berhasil dikirim: {response.status_code}"})
            except requests.exceptions.RequestException as e:
                return JsonResponse({"success": False, "message": f"Gagal terhubung ke teman: {e}"})

    return JsonResponse({"success": False, "message": "Metode tidak diperbolehkan."}, status=405)



from django.http import JsonResponse
from .models import DatasetRequest

def api_request_list(request):
    dataset_requests = DatasetRequest.objects.all().select_related("dataset")

    result = []
    for req in dataset_requests:
        item = {
            "id": req.id,
            "nama_model": req.nama_model,
            "kebutuhan": req.kebutuhan,
            "deskripsi": req.deskripsi,
            "timestamp": req.timestamp.strftime("%Y-%m-%d %H:%M"),
            "dataset": None
        }

        if req.dataset:
            item["dataset"] = {
                "id": req.dataset.id,
                "name": req.dataset.name,
                "description": req.dataset.description,
                "status": req.dataset.status,
                "data_file": request.build_absolute_uri(req.dataset.data_file.url) if req.dataset.data_file else None
            }

        result.append(item)

    return JsonResponse({"success": True, "data": result})


from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def list_dataset_sent(request):
    from .models import DatasetSent
    from .serializers import DatasetSentSerializer

    data = DatasetSent.objects.all().order_by('-timestamp')
    serializer = DatasetSentSerializer(data, many=True)
    return Response({"success": True, "data": serializer.data})



# MOBILE
from rest_framework import viewsets
from rest_framework import permissions
from .models import Dataset, DatasetRequest, DatasetSent
from .serializers import DatasetSerializer, DatasetRequestSerializer, DatasetSentSerializer

# ViewSet untuk Dataset
class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dataset.objects.all().order_by("-uploaded_at")
    serializer_class = DatasetSerializer
    permission_classes = [permissions.AllowAny]  # Jika public API

# ViewSet untuk DatasetRequest
class DatasetRequestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatasetRequest.objects.all()
    serializer_class = DatasetRequestSerializer
    permission_classes = [permissions.AllowAny]

# ViewSet untuk DatasetSent (opsional)
class DatasetSentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatasetSent.objects.all()
    serializer_class = DatasetSentSerializer
    permission_classes = [permissions.AllowAny]


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import DatasetRequest, Dataset

@api_view(['POST'])
def konfirmasi_dataset(request, request_id, dataset_id):
    try:
        req = DatasetRequest.objects.get(id=request_id)
        dataset = Dataset.objects.get(id=dataset_id)
        req.dataset = dataset
        req.save()
        return Response({"message": "Dataset dikaitkan."})
    except DatasetRequest.DoesNotExist:
        return Response({"error": "Request tidak ditemukan."}, status=404)
    except Dataset.DoesNotExist:
        return Response({"error": "Dataset tidak ditemukan."}, status=404)


# mobile bisa mengirim ke web creation
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import requests

@api_view(['POST'])
def kirim_dataset_ke_teman(request):
    dataset_id = request.query_params.get('dataset_id')
    request_id = request.query_params.get('request_id')
    print("Received dataset_id:", dataset_id, "request_id:", request_id)

    if not dataset_id or not request_id:
        return Response({"success": False, "message": "dataset_id dan request_id wajib diisi."}, status=400)

    try:
        dataset = Dataset.objects.get(id=dataset_id)
    except Dataset.DoesNotExist:
        return Response({"success": False, "message": "Dataset tidak ditemukan."}, status=404)

    try:
        dataset_request = DatasetRequest.objects.get(id=request_id)
    except DatasetRequest.DoesNotExist:
        return Response({"success": False, "message": "Permintaan tidak ditemukan."}, status=404)

    dataset_request.dataset = dataset
    dataset_request.save()

    # Buka file CSV
    file_path = dataset.data_file.path
    with open(file_path, 'rb') as f:
        files = {
            'file': (dataset.data_file.name, f, 'text/csv'),
        }
        data = {
            'dataset_id': dataset.id,
            'request_id': dataset_request.id,
            'name': dataset.name,
            'description': dataset.description,
            'status': dataset.status,
            'nama_model': dataset_request.nama_model,
            'kebutuhan': dataset_request.kebutuhan,
        }

        try:
            response = requests.post(
                "http://10.40.28.65:8000/api/terima-dataset/",
                files=files,
                data=data,
                timeout=10
            )
            if response.status_code == 200:
                return Response({"success": True, "message": "Dataset berhasil dikirim ke server teman."})
            else:
                return Response({"success": False, "message": f"Gagal kirim ke teman: status {response.status_code}"})
        except requests.exceptions.RequestException as e:
            return Response({"success": False, "message": f"RequestException: {e}"})
