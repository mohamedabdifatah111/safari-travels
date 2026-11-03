from django.db import models


class Destination(models.Model):
    """A place customers can travel to. Only active destinations are public."""

    name = models.CharField(max_length=120)
    country = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    # Optional: the API returns null when no image has been uploaded.
    image = models.ImageField(upload_to="destinations/", blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this destination from the website.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active", "name"], name="dest_active_name_idx"),
        ]

    def __str__(self):
        return f"{self.name}, {self.country}"