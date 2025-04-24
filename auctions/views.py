from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from .models import User, Listing, Bid, Comment, Category, Watchlist
from .forms import ListingForm, BidForm, CommentForm


def index(request):
    listings = Listing.objects.filter(is_active=True)
    # Check each listing's end_date
    for listing in listings:
        listing.is_still_active()
    listing = Listing.objects.filter(is_active=True) # Refresh after checking
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("auctions:index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("auctions:index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.creator = request.user
            listing.current_price = listing.starting_bid
            listing.save() # This will trigger the save method to set end_date
            return HttpResponseRedirect(reverse("auctions:index"))
    else:
        form = ListingForm()
    return render(request, "auctions/create.html", {"form": form})


@login_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.user != listing.creator:
        raise PermissionDenied("You are not authorized to edit this listing.")
    if not listing.is_active:
        raise PermissionDenied("Cannot edit a closed listing.")

    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            updated_listing = form.save(commit=False)
            # Update current_price if starting_bid changes
            if updated_listing.starting_bid > updated_listing.current_price:
                updated_listing.current_price = updated_listing.starting_bid
            updated_listing.save()
            return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
    else:
        form = ListingForm(instance=listing)

    return render(request, "auctions/edit.html", {
        "form": form,
        "listing": listing
    })


def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    listing.is_still_active() # Check if auction is still active
    bid_form = BidForm(listing=listing)
    comment_form = CommentForm()
    is_watching = False
    has_won = False

    if request.user.is_authenticated:
        is_watching = Watchlist.objects.filter(user=request.user, listing=listing).exists()
        if not listing.is_active and listing.bids.exists():
            highest_bid = listing.bids.order_by('-amount').first()
            if highest_bid.bidder == request.user:
                has_won = True
    
    if request.method == "POST":
        if 'bid' in request.POST and request.user.is_authenticated and listing.is_active:
            bid_form = BidForm(request.POST, listing=listing)
            if bid_form.is_valid():
                bid = bid_form.save(commit=False)
                if bid.amount > listing.current_price and bid.amount >= listing.starting_bid:
                    bid.bidder = request.user
                    bid.listing = listing
                    bid.save()
                    listing.current_price = bid.amount
                    listing.save()
                    messages.success(request, "Your bid was successfully placed!")
                    return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
                else:
                    messages.error(request, f"Your bid must be higher than the current price of ₵{listing.current_price:.2f} and least the starting bid of ₵{listing.starting_bid:.2f}.")
            else:
                messages.error(request, "Please enter a valid bid amount. (e.g. 30)")
        
        elif 'comment' in request.POST and request.user.is_authenticated:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.author = request.user
                comment.listing = listing
                comment.save()
                return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
        
        elif 'watchlist' in request.POST and request.user.is_authenticated:
            if is_watching:
                Watchlist.objects.filter(user=request.user, listing=listing).delete()
            else:
                Watchlist.objects.create(user=request.user, listing=listing)
            return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
        
        elif 'close' in request.POST and request.user == listing.creator and listing.is_active:
            listing.is_active = False
            listing.save()
            return HttpResponseRedirect(reverse("auctions:listing", args=[listing_id]))
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "comments": listing.comments.all(),
        "is_watching": is_watching,
        "has_won": has_won
    })


@login_required
def watchlist(request):
    watchlist_items = Watchlist.objects.filter(user=request.user)
    # Check each listing's end_date
    for item in watchlist_items:
        item.listing.is_still_active()
    return render(request, "auctions/watchlist.html", {
        "watchlist_items": watchlist_items
    })


def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })


def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = Listing.objects.filter(category=category, is_active=True)
    # Check each listing's end_date
    for listing in listings:
        listing.is_still_active()
    listings = Listing.objects.filter(category=category, is_active=True) # Refresh
    return render(request, "auctions/index.html", {
        "listings": listings,
        "category": category
    })


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password was successfully updated!")
            return HttpResponseRedirect(reverse("auctions:index"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "auctions/change_password.html", {
        "form": form
    })