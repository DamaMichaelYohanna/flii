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
    if not doc.file or not os.path.exists(doc.file.path):
        raise Http404("Document file does not exist.")
    return FileResponse(open(doc.file.path, 'rb'), as_attachment=True, filename=os.path.basename(doc.file.name))
