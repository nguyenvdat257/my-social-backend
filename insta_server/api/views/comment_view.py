from .my_imports import *


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request):
    post = get_object_or_404(Post, code=request.data['post_code'])
    profile = request.user.profile
    data = {'post': post.id, 'profile': profile.id, 'reply_to_comment': request.data.get(
        'reply_to_comment'), 'body': request.data['body']}
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response('Cannot create comment', status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.profile == request.user.profile:
        comment.delete()
        return Response('Successfully delete comment')
    else:
        return Response('Cannot delete comment', status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_comments(request, post_code): # 'comments/<str:post_code>'
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.COMMENT_PAGE_SIZE
    post = get_object_or_404(Post, code=post_code)
    result_set = paginator.paginate_queryset(post.comment_set, request)
    serializer = CommentSerializer(result_set, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def like_unlike_comment(request):
    comment = get_object_or_404(Comment, pk=request.data['id'])
    comment_like = CommentLike.objects.filter(profile=request.user.profile, comment=comment)
    if comment_like:
        comment_like.delete()
        likes_count = comment.commentlike_set.count()
        comment.likes_count=likes_count
        comment.save()
        return Response(data={'type': 'unlike', 'likes_count': likes_count})
    else:
        CommentLike.objects.create(profile=request.user.profile, comment=comment)
        likes_count = comment.commentlike_set.count()
        comment.likes_count=likes_count
        comment.save()
        return Response(data={'type': 'like', 'likes_count': likes_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comment_like_profile(request, pk): # 'comments/like-profile/<int:pk>'
    paginator = pagination.CursorPagination()
    paginator.page_size = settings.COMMENT_LIKE_PAGE_SIZE
    paginator.ordering = 'name'
    comment_like_profiles = Profile.objects.filter(comment_like__comment=pk)
    result_set = paginator.paginate_queryset(comment_like_profiles, request)
    serializer = ProfileLightSerializer(result_set, many=True)
    return paginator.get_paginated_response(serializer.data)