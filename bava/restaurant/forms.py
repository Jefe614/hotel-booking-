# restaurant/forms.py
from django import forms
from .models import Reservation, MenuItem

from django import forms
from .models import Reservation, Table

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer_name', 'customer_email', 'customer_phone', 
                 'number_of_guests', 'reservation_date', 'reservation_time',
                 'table', 'special_requests']
        
        widgets = {
            'reservation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reservation_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get available tables and order them by capacity
        self.fields['table'].queryset = Table.objects.filter(is_available=True).order_by('capacity')
        
        # Add Bootstrap classes to all fields
        for field in self.fields:
            if field == 'table':
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            elif field != 'special_requests':  # special_requests already has its class
                self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        table = cleaned_data.get('table')
        number_of_guests = cleaned_data.get('number_of_guests')
        reservation_date = cleaned_data.get('reservation_date')
        reservation_time = cleaned_data.get('reservation_time')
        
        # Validate number of guests vs table capacity
        if table and number_of_guests:
            if number_of_guests > table.capacity:
                raise forms.ValidationError(
                    f"This table only accommodates {table.capacity} guests. "
                    f"Please select a larger table or reduce your party size."
                )
        
        # Check for existing reservations at the same time
        if table and reservation_date and reservation_time:
            conflicting_reservations = Reservation.objects.filter(
                table=table,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                is_confirmed=True
            ).exists()
            
            if conflicting_reservations:
                raise forms.ValidationError(
                    "This table is already booked at the selected time. "
                    "Please choose a different time or table."
                )
        
        return cleaned_data

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BookingForm(forms.Form):
    customer_name = forms.CharField(max_length=100)
    customer_email = forms.EmailField()
    customer_phone = forms.CharField(max_length=15)
    number_of_guests = forms.IntegerField()
    reservation_date = forms.DateField(widget=forms.SelectDateWidget())
    reservation_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    table = forms.ChoiceField(choices=[('1', 'Table 1'), ('2', 'Table 2')]) 
    special_requests = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to each field
        self.fields['customer_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['customer_email'].widget.attrs.update({'class': 'form-control'})
        self.fields['customer_phone'].widget.attrs.update({'class': 'form-control'})
        self.fields['number_of_guests'].widget.attrs.update({'class': 'form-control'})
        self.fields['reservation_date'].widget.attrs.update({'class': 'form-control'})
        self.fields['reservation_time'].widget.attrs.update({'class': 'form-control'})
        self.fields['table'].widget.attrs.update({'class': 'form-select'})
        self.fields['special_requests'].widget.attrs.update({'class': 'form-control'})