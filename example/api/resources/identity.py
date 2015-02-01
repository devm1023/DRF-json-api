from django.contrib.auth import models as auth_models
from rest_framework import viewsets, generics, renderers, parsers
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework_ember import mixins, utils
from ..serializers.identity import IdentitySerializer
from ..serializers.post import PostSerializer


class Identity(mixins.MultipleIDMixin, viewsets.ModelViewSet):
    queryset = auth_models.User.objects.all()
    serializer_class = IdentitySerializer

    # demonstrate sideloading data for use at app boot time
    @list_route()
    def posts(self, request):
        self.resource_name = False

        identities = self.queryset
        posts = [{'id': 1, 'title': 'Test Blog Post'}]

        data = {
            u'identities': IdentitySerializer(identities, many=True).data,
            u'posts': PostSerializer(posts, many=True).data,
        }
        return Response(utils.format_keys(data, format_type='camelize'))

    @detail_route()
    def manual_resource_name(self, request, *args, **kwargs):
        self.resource_name = 'data'
        return super(Identity, self).retrieve(request, args, kwargs)


class GenericIdentity(generics.GenericAPIView):
    """
    Current user's identity endpoint.

    GET /identities/generic
    """
    serializer_class = IdentitySerializer
    allowed_methods = ['GET']
    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.JSONParser, )


    def get_queryset(self):
        return auth_models.User.objects.all()

    def get(self, request, pk=None):
        """
        GET request
        """
        obj = self.get_object()
        return Response(IdentitySerializer(obj).data)

