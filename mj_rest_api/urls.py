from django.conf.urls import patterns, include, url
from django.contrib import admin

from moviejournal import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mj_rest_api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^login/$', views.login, name="login"),
    url(r'^register/$', views.register, name="register"),
    url(r'^admin/$', include(admin.site.urls)),
    url(r'^user/$', views.user),
    url(r'^user/(?P<user_id>\d+)/$', views.user),
    url(r'^movie/(?P<movie_id>\d+)/$', views.movie, name='movie'),
    url(r'^screening/(?P<screening_id>\d+)/$', views.screening),
    url(r'^screening/$', views.screening),
    url(r'^user/(?P<user_id>\d+)/journal/$', views.journal),
    url(r'^watchlist_entry/(?P<watchlist_entry_id>\d+)/$', views.watchlist_entry),
    url(r'^watchlist_entry/$', views.watchlist_entry),
    url(r'^user/(?P<user_id>\d+)/watchlist/$', views.watchlist),
)
