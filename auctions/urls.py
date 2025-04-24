from django.urls import path

from . import views

app_name = "auctions"

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("listing/<int:listing_id>", views.listing, name="listing"),
    path("listing/<int:listing_id>/edit", views.edit_listing, name="edit_listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("categories", views.categories, name="categories"),
    path("category/<int:category_id>", views.category_listings, name="category_listings"),
    path("change-password", views.change_password, name="change_password"),
]
