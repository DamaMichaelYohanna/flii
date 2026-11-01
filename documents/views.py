import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Document

@login_required
def document_list(request):
    user = request.user
    docs = user.documents.all()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('document_type', 'cv')
        uploaded_file = request.FILES.get('file')

        if uploaded_file and title:
            doc = Document.objects.create(
                user=user,
                title=title,
                document_type=doc_type,
                file=uploaded_file,
                notes=request.POST.get('notes', ''),
                verification_status='verified'
            )
            messages.success(request, f"Document '{doc.title}' successfully uploaded to your Document Vault.")
            return redirect('documents:list')
        else:
            messages.error(request, "Please provide a document title and select a valid file.")

    context = {
        'documents': docs,
        'doc_types': Document.DOCUMENT_TYPES,
        'total_count': docs.count(),
    }
    return render(request, 'documents/list.html', context)


@login_required
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    title = doc.title
    doc.file.delete(save=False)
    doc.delete()
    messages.info(request, f"Document '{title}' deleted from Document Vault.")
    return redirect('documents:list')


@login_required
def document_download(request, pk):
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    if not doc.file:
        raise Http404("Document file does not exist.")
    
    # Check for local filesystem storage
    try:
        if hasattr(doc.file, 'path') and os.path.exists(doc.file.path):
            return FileResponse(open(doc.file.path, 'rb'), as_attachment=True, filename=os.path.basename(doc.file.name))
    except Exception:
        pass

    # Remote storage URL (e.g., Cloudinary in production)
    try:
        url = doc.file.url
        if url and (url.startswith('http://') or url.startswith('https://')):
            if 'res.cloudinary.com' in url and '/upload/' in url:
                ext = doc.file_extension
                if ext == 'pdf':
                    download_url = url.replace('/upload/', '/upload/fl_attachment/') + '.png'
                elif ext:
                    download_url = url.replace('/upload/', '/upload/fl_attachment/') + f'.{ext}'
                else:
                    download_url = url.replace('/upload/', '/upload/fl_attachment/')
                return redirect(download_url)
            return redirect(url)
    except Exception:
        pass

    raise Http404("Document file could not be located.")


@login_required
def document_view(request, pk):
    """Serve document inline for browser previewing."""
    doc = get_object_or_404(Document, pk=pk, user=request.user)
    if not doc.file:
        raise Http404("Document file does not exist.")
    
    # Check local filesystem storage with inline disposition
    try:
        if hasattr(doc.file, 'path') and os.path.exists(doc.file.path):
            import mimetypes
            content_type, _ = mimetypes.guess_type(doc.file.path)
            content_type = content_type or 'application/octet-stream'
            return FileResponse(open(doc.file.path, 'rb'), content_type=content_type, as_attachment=False, filename=os.path.basename(doc.file.name))
    except Exception:
        pass

    # Remote storage URL (e.g., Cloudinary in production)
    try:
        url = doc.file.url
        if url and (url.startswith('http://') or url.startswith('https://')):
            if 'res.cloudinary.com' in url:
                ext = doc.file_extension
                if ext == 'pdf':
                    # Cloudinary converts PDF pages into high-res PNG preview
                    preview_url = url + '.png' if not url.endswith('.png') else url
                    return redirect(preview_url)
                elif ext in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg']:
                    img_url = url + f'.{ext}' if not url.endswith(f'.{ext}') else url
                    return redirect(img_url)
            return redirect(url)
    except Exception:
        pass

    raise Http404("Document file could not be located.")

