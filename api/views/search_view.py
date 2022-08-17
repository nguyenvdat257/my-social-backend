from .my_imports import *


@api_view(['GET'])
def search_hashtag(request, keyword):
    hashtags = HashTag.objects.filter(body__contains=keyword)[:20]
    serializer = HashtagSerializer(hashtags, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE', 'POST'])
def process_recent_search(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            recent_searchs = RecentSearch.objects.filter(
                current_profile=request.user.profile).order_by('-modified')
            serializer = RecentSearchSerializer(recent_searchs, context={'profile': request.user.profile}, many=True)
            return Response(serializer.data)
        else:
            return Response([])
    if request.method == 'DELETE':
        if request.user.is_authenticated:
            RecentSearch.objects.filter(
                current_profile=request.user.profile).all().delete()
            return Response('Successfully delete search')
    if request.method == 'POST':
        if request.user.is_authenticated:
            if 'search_profile' in request.data:
                RecentSearch.objects.update_or_create(
                    current_profile=request.user.profile, search_profile_id=request.data['search_profile'])
            if 'search_hashtag' in request.data:
                RecentSearch.objects.update_or_create(
                    current_profile=request.user.profile, search_hashtag_id=request.data['search_hashtag'])
            recent_searchs = RecentSearch.objects.filter(
                current_profile=request.user.profile).order_by('-modified')
            serializer = RecentSearchSerializer(recent_searchs, context={'profile': request.user.profile}, many=True)
            return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_search(request, pk):
    search = get_object_or_404(RecentSearch, pk=pk)
    if search.current_profile == request.user.profile:
        search.delete()
        return Response('Successfully delete search')
    else:
        return Response('Cannot delete search', status=status.HTTP_400_BAD_REQUEST)
