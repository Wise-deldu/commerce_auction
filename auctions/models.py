from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='listings/', blank=True, null=True)
    image_url = models.URLField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    duration_days = models.PositiveIntegerField(default=7)
    end_date = models.DateTimeField(null=True, blank=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        #Calculate end_date when saving if duration_days is set
        if self.duration_days and not self.end_date:
            self.end_date = self.created_at + timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

    
    def is_still_active(self):
        # Check if the listing is active based on end_date
        if not self.is_active or (self.end_date and timezone.now() > self.end_date):
            self.is_active = False
            self.save()
            return False
        return True
    

    def get_image_source(self):
        """Return the image URL to display: uploaded image if present, else image_url."""
        if self.image:
            return self.image.url
        return self.image_url or ''


    def __str__(self):
        return self.title


class Bid(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.amount} on {self.listing}"


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.listing}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}'s watchlist: {self.listing}"
