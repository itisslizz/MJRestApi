<!DOCTYPE html>
<html>
<head>

</head>


<table>
    <tr>
        <td>Resource</td><td>URL</td><td>Methods</td>
    </tr>
    <tr>
        <td></td><td>URL</td><td>Methods</td>
    </tr>
    <tr>
        <td>Resource</td><td>URL</td><td>Methods</td>
    </tr>

</table>

    url(r'^login/$', views.login, name="login"),
    url(r'^register/$', views.register, name="register"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^movie/(?P<movie_id>\d+)/$', views.movie, name='movie'),
    url(r'^screening/(?P<screening_id>\d+)/$', views.screening),
    url(r'^screening/$', views.screening),
    url(r'^user/(?P<user_id>\d+)/journal/$', views.journal),