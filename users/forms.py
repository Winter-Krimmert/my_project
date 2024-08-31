from django import forms
from django.forms import formset_factory

class IngredientForm(forms.Form):
    name = forms.CharField(max_length=255)
    quantity = forms.CharField(max_length=255)
    unit = forms.CharField(max_length=50, required=False)
    spoonacular_id = forms.CharField(max_length=50, required=False)

class InstructionForm(forms.Form):
    step_number = forms.IntegerField()
    description = forms.CharField(widget=forms.Textarea)
    photo = forms.URLField(required=False)
    video = forms.URLField(required=False)

class RecipeForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea)
    keywords = forms.CharField(max_length=255, required=False)
    servings = forms.IntegerField()
    cook_time = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        # Add any additional validation here if necessary
        return cleaned_data

# Define formsets
IngredientFormSet = formset_factory(IngredientForm, extra=1)  # Adjust `extra` as needed
InstructionFormSet = formset_factory(InstructionForm, extra=1)  # Adjust `extra` as needed
