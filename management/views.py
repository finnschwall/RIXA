from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
# from . import database
from rixarag import database


@login_required(login_url="about")
def index(request):
    """Home page view showing collection selection."""
    collections = database.list_collections()
    collection_info = []
    for collection in collections:
        collection_info.append({"name": collection, "count": database.get_element_count(collection)})

    return render(request, 'rag_viewer/index.html', {'collections': collection_info})


@login_required(login_url="about")
def view_collection(request, collection_name):
    """View for displaying random elements and allowing queries within a collection."""
    # Get random elements to display

    query_results = None
    query = request.GET.get('query', '')
    n_results = request.GET.get('n', 5)
    key = request.GET.get('key', '')
    value = request.GET.get('value', '')


    if not n_results:
        n_results = 3
    else:
        n_results = int(n_results)
    if key:
        keys = request.GET.getlist('key')
        values = request.GET.getlist('value')
        query_dict = {key: value for key, value in zip(keys, values)}

        query_results = database.query_by_metadata(query_dict, collection_name, count=n_results)
        query_results["distances"] = [0] * len(query_results["ids"])

        context = {
            'collection_name': collection_name,
            'query_results': query_results,
            'key': key,
            'value': value,
            "n_results": n_results,
            "failed" : len(query_results["ids"]) == 0
        }

    elif query:
        query_results = database.query(query, collection_name, n_results=n_results)
        context = {
            'collection_name': collection_name,
            'query_results': query_results,
            'query': query,
            "n_results": n_results,
            "failed": len(query_results["ids"]) == 0
        }
    else:
        random_results = database.get_random_elements(count=n_results, collection=collection_name)

        context = {
            'collection_name': collection_name,
            'random_results': random_results,
            'query_results': query_results,
        }
    return render(request, 'rag_viewer/collection.html', context)


def perform_query(request, collection_name):
    """AJAX view for performing queries."""
    if request.method == 'POST':
        query = request.POST.get('query', '')
        if query:
            results = database.query(query, collection_name, n_results=5)
            return JsonResponse(results)
    return JsonResponse({'error': 'Invalid request'}, status=400)