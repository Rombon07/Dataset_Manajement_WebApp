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
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
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


# @login_required
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
            request.session["dataset_info"] = form.cleaned_data
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


@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action="view_detail")

    preview_html, bar_plot_html, box_plot_html = None, None, None

    try:
        if dataset.data_file and os.path.exists(dataset.data_file.path):
            df = pd.read_csv(dataset.data_file.path, nrows=10)
            preview_html = df.to_html(
                classes=["table", "table-striped", "table-bordered", "text-center"]
            )
            numeric_cols = df.select_dtypes(include="number").columns.tolist()

            if numeric_cols:
                fig_bar = px.bar(
                    df,
                    x=df.index,
                    y=numeric_cols[0],
                    title=f"Bar Chart - {numeric_cols[0]}",
                )
                bar_plot_html = plot(fig_bar, output_type="div")

                fig_box = go.Figure()
                for col in numeric_cols:
                    fig_box.add_trace(go.Box(y=df[col], name=col))
                fig_box.update_layout(title="Boxplot Data Numerik")
                box_plot_html = plot(fig_box, output_type="div")
    except Exception as e:
        preview_html = f"<p class='text-danger'>Gagal memuat file: {str(e)}</p>"

    logs = (
        DownloadLog.objects.filter(dataset=dataset)
        .select_related("user")
        .order_by("-timestamp")
    )
    return render(
        request,
        "dataset/dataset_detail.html",
        {
            "dataset": dataset,
            "preview": preview_html,
            "bar_plot": bar_plot_html,
            "box_plot": box_plot_html,
            "logs": logs,
        },
    )


# @login_required
# def dataset_detail(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)
#     DownloadLog.objects.create(user=request.user, dataset=dataset, action="view_detail")

#     preview_html = None

#     try:
#         if dataset.data_file and os.path.exists(dataset.data_file.path):
#             df = pd.read_csv(dataset.data_file.path, nrows=10)
#             preview_html = df.to_html(
#                 classes=["table", "table-striped", "table-bordered", "text-center"]
#             )

#             # Nonaktifkan bar dan box plot
#             # numeric_cols = df.select_dtypes(include="number").columns.tolist()

#             # if numeric_cols:
#             #     fig_bar = px.bar(
#             #         df,
#             #         x=df.index,
#             #         y=numeric_cols[0],
#             #         title=f"Bar Chart - {numeric_cols[0]}",
#             #     )
#             #     bar_plot_html = plot(fig_bar, output_type="div")

#             #     fig_box = go.Figure()
#             #     for col in numeric_cols:
#             #         fig_box.add_trace(go.Box(y=df[col], name=col))
#             #     fig_box.update_layout(title="Boxplot Data Numerik")
#             #     box_plot_html = plot(fig_box, output_type="div")

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
#             "bar_plot": None,  # Kosongkan variabel plot
#             "box_plot": None,
#             "logs": logs,
#         },
#     )


# @login_required
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


# @login_required
# def download_summary(request, dataset_id):
#     dataset = get_object_or_404(Dataset, id=dataset_id)
#     DownloadLog.objects.create(
#         user=request.user, dataset=dataset, action="download_summary"
#     )

#     try:
#         df = pd.read_csv(dataset.data_file.path, nrows=10)
#         preview_html = df.to_html(
#             classes=["table", "table-bordered", "table-sm"], index=False
#         )

#         numeric_cols = df.select_dtypes(include="number").columns.tolist()
#         chart_base64, boxplot_base64 = None, None

#         if numeric_cols:
#             # Bar chart
#             fig, ax = plt.subplots(figsize=(6, 4))
#             df[numeric_cols[0]].plot(kind="bar", ax=ax, color="#4B0082")
#             ax.set_title(f"Bar Chart - {numeric_cols[0]}")
#             plt.tight_layout()
#             buf = io.BytesIO()
#             plt.savefig(buf, format="png")
#             plt.close(fig)
#             chart_base64 = (
#                 f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
#             )

#             # Boxplot
#             fig, ax = plt.subplots(figsize=(6, 4))
#             df[numeric_cols].plot(kind="box", ax=ax)
#             ax.set_title("Boxplot Data Numerik")
#             plt.tight_layout()
#             buf = io.BytesIO()
#             plt.savefig(buf, format="png")
#             plt.close(fig)
#             boxplot_base64 = (
#                 f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
#             )
#     except Exception as e:
#         preview_html = f"<p class='text-danger'>Gagal memuat file: {str(e)}</p>"
#         chart_base64 = boxplot_base64 = None

#     logs = (
#         DownloadLog.objects.filter(dataset=dataset)
#         .select_related("user")
#         .order_by("-timestamp")
#     )
#     html_string = render_to_string(
#         "dataset/summary_pdf.html",
#         {
#             "dataset": dataset,
#             "preview": preview_html,
#             "chart_base64": chart_base64,
#             "boxplot_base64": boxplot_base64,
#             "logs": logs,
#             "user": request.user,
#         },
#     )

#     response = HttpResponse(content_type="application/pdf")
#     response["Content-Disposition"] = (
#         f'attachment; filename="{dataset.name}_summary.pdf"'
#     )
#     pisa_status = pisa.CreatePDF(src=html_string, dest=response)

#     if pisa_status.err:
#         return HttpResponse("Terjadi kesalahan saat membuat PDF", status=500)
#     return response


# def print_dataset(request, pk):
#     dataset = get_object_or_404(Dataset, pk=pk)

#     # Load file CSV atau XLSX
#     file_path = dataset.data_file.path
#     if file_path.endswith(".csv"):
#         df = pd.read_csv(file_path)
#     elif file_path.endswith(".xlsx"):
#         df = pd.read_excel(file_path)
#     else:
#         df = pd.DataFrame()

#     # Preview tabel (gunakan DataFrame to_html)
#     preview_html = df.head(10).to_html(classes="table table-bordered", index=False)

#     # Bar Chart
#     chart_base64 = None
#     if not df.empty and df.select_dtypes(include="number").shape[1] > 0:
#         fig, ax = plt.subplots(figsize=(6, 4))
#         df.select_dtypes(include="number").head(10).plot(kind="bar", ax=ax)
#         plt.tight_layout()
#         buf = BytesIO()
#         plt.savefig(buf, format="png")
#         buf.seek(0)
#         image_base64 = base64.b64encode(buf.read()).decode("utf-8")
#         chart_base64 = "data:image/png;base64," + image_base64
#         plt.close()

#     # Boxplot
#     boxplot_base64 = None
#     if not df.empty and df.select_dtypes(include="number").shape[1] > 0:
#         fig2, ax2 = plt.subplots(figsize=(6, 4))
#         df.select_dtypes(include="number").plot(kind="box", ax=ax2)
#         plt.tight_layout()
#         buf2 = BytesIO()
#         plt.savefig(buf2, format="png")
#         buf2.seek(0)
#         image2_base64 = base64.b64encode(buf2.read()).decode("utf-8")
#         boxplot_base64 = "data:image/png;base64," + image2_base64
#         plt.close()

#     # Log interaksi pengguna (jika ada)
#     logs = DownloadLog.objects.filter(dataset=dataset).order_by("-timestamp")

#     return render(
#         request,
#         "dataset/print_dataset.html",
#         {
#             "dataset": dataset,
#             "preview": preview_html,
#             "chart_base64": chart_base64,
#             "boxplot_base64": boxplot_base64,
#             "logs": logs,
#         },
#     )



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


@login_required
def api_dataset(request, dataset_id):
    dataset = get_object_or_404(Dataset, id=dataset_id)
    DownloadLog.objects.create(user=request.user, dataset=dataset, action="api")
    return JsonResponse(
        {
            "name": dataset.name,
            "description": dataset.description,
            "download_url": dataset.data_file.url,
        }
    )


def test_404(request):
    return render(request, "404.html", status=404)
