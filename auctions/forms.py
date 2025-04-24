from django import forms
from django.core.exceptions import ValidationError
from .models import Listing, Bid, Comment

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image', 'image_url', 'category', 'duration_days']
        widgets = {
            'duration_days': forms.NumberInput(attrs={'min': '1', 'max': '30'}), # Ensures input is a number
            'image': forms.FileInput(),
            'image_url': forms.URLInput(),
        }
        help_texts = {
            'image': 'Upload an image file (or provide a URL below).',
            'image_url': 'A valid URL to an image is required.',
        }


    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')

        if not image and not image_url:
            raise ValidationError("You must provide either an image upload or an image URL.")
        if image and image_url:
            raise ValidationError("Please provide only one: either an image upload or an image URL, not both.")

        return cleaned_data

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0.01',
                'required': True
            })
        }
    
    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.listing:
            if amount <= self.listing.current_price:
                raise ValidationError(f"Your bid must be higher than the current price of ₵{self.listing.current_price:.2f}.")
            if amount < self.listing.starting_bid:
                raise ValidationError(f"Your bid must be at least the starting bid of ₵{self.listing.starting_bid:.2f}.")
        return amount


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'rows': 3})}