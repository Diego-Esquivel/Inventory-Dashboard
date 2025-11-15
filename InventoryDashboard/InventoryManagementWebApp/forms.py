from django import forms

class CreateInventoryProductForm(forms.Form):
    label_id = forms.CharField(max_length=100, label='Label ID', required=True, min_length=1)
    storage_location = forms.CharField(max_length=4, label='Storage Location', initial='HOLD', required=True)
    quantity_on_pallet = forms.IntegerField(label='Quantity on Pallet', initial=-100, required=True)
    product_description = forms.CharField(max_length=200, label='Product Description', required=False)

class ReadInventoryProductsForm(forms.Form):
    label_id = forms.CharField(max_length=100, label='Label ID', required=False)
    storage_location = forms.CharField(max_length=4, label='Storage Location', required=False)
    quantity_on_pallet = forms.IntegerField(label='Quantity on Pallet', required=False)
    product_description = forms.CharField(max_length=200, label='Product Description', required=False)
    scheduled_for_deletion = forms.BooleanField(label='Scheduled for Deletion', required=False)

class UpdateInventoryProductLocationForm(forms.Form):
    new_location = forms.CharField(max_length=4, label='New Storage Location')

class UpdateInventoryProductQuantityForm(forms.Form):
    new_quantity = forms.IntegerField(label='New Quantity on Pallet', required=False)
    increase_quantity = forms.IntegerField(label='Increase Quantity By', required=False)

class DeleteInventoryProductForm(forms.Form):
    confirmation = forms.BooleanField(label='Confirm Deletion')