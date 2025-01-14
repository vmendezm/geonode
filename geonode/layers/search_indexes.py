#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from pinax.ratings.models import OverallRating
from dialogos.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from haystack import indexes
from geonode.maps.models import Layer


class LayerIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField(model_attr='resourcebase_ptr_id')
    abstract = indexes.CharField(model_attr="abstract", boost=1.5)
    category__gn_description = indexes.CharField(model_attr="category__gn_description", null=True)
    csw_type = indexes.CharField(model_attr="csw_type")
    csw_wkt_geometry = indexes.CharField(model_attr="csw_wkt_geometry")
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    owner__username = indexes.CharField(model_attr="owner", faceted=True, null=True)
    is_published = indexes.BooleanField(model_attr="is_published")
    featured = indexes.BooleanField(model_attr="featured")
    srid = indexes.CharField(model_attr="srid")
    supplemental_information = indexes.CharField(model_attr="supplemental_information", null=True)
    thumbnail_url = indexes.CharField(model_attr="thumbnail_url", null=True)
    uuid = indexes.CharField(model_attr="uuid")
    title = indexes.CharField(model_attr="title", boost=2)
    date = indexes.DateTimeField(model_attr="date")

    text = indexes.EdgeNgramField(document=True, use_template=True, stored=False)
    type = indexes.CharField(faceted=True)
    subtype = indexes.CharField(faceted=True)
    alternate = indexes.CharField(model_attr='alternate')
    title_sortable = indexes.CharField(indexed=False, stored=False)  # Necessary for sorting
    category = indexes.CharField(
        model_attr="category__identifier",
        faceted=True,
        null=True,
        stored=True)
    bbox_left = indexes.FloatField(model_attr="bbox_x0", null=True, stored=False)
    bbox_right = indexes.FloatField(model_attr="bbox_x1", null=True, stored=False)
    bbox_bottom = indexes.FloatField(model_attr="bbox_y0", null=True, stored=False)
    bbox_top = indexes.FloatField(model_attr="bbox_y1", null=True, stored=False)
    temporal_extent_start = indexes.DateTimeField(
        model_attr="temporal_extent_start",
        null=True,
        stored=False)
    temporal_extent_end = indexes.DateTimeField(
        model_attr="temporal_extent_end",
        null=True,
        stored=False)
    keywords = indexes.MultiValueField(
        model_attr="keyword_slug_list",
        null=True,
        faceted=True,
        stored=True)
    regions = indexes.MultiValueField(
        model_attr="region_name_list",
        null=True,
        faceted=True,
        stored=True)
    popular_count = indexes.IntegerField(
        model_attr="popular_count",
        default=0,
        boost=20)
    share_count = indexes.IntegerField(model_attr="share_count", default=0)
    rating = indexes.IntegerField(null=True)
    num_ratings = indexes.IntegerField(stored=False)
    num_comments = indexes.IntegerField(stored=False)

    def get_model(self):
        return Layer

    def prepare_type(self, obj):
        return "layer"

    def prepare_subtype(self, obj):
        if obj.subtype == "vector":
            if obj.has_time:
                return "vector_time"
            else:
                return "vector"
        elif obj.subtype == "raster":
            return "raster"
        elif obj.subtype in ['tileStore', 'remote']:
            return "remote"

    def prepare_rating(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            rating = OverallRating.objects.filter(
                object_id=obj.pk,
                content_type=ct
            ).aggregate(r=Avg("rating"))["r"]
            return float(str(rating or "0"))
        except OverallRating.DoesNotExist:
            return 0.0

    def prepare_num_ratings(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            return OverallRating.objects.filter(
                object_id=obj.pk,
                content_type=ct
            ).all().count()
        except OverallRating.DoesNotExist:
            return 0

    def prepare_num_comments(self, obj):
        try:
            return Comment.objects.filter(
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj)
            ).all().count()
        except Exception:
            return 0

    def prepare_title_sortable(self, obj):
        return obj.title.lower()
