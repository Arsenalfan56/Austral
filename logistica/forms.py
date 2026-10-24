# logistica/forms.py
# logistica/forms.py
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import RegistroCalibracion, OrdenVibracion, DiagnosticoPredictivo, RegistroInforme


# ==========================================
# FORMULARIOS EXISTENTES (Modelo)
# ==========================================

class RegistroCalibracionForm(forms.ModelForm):
    codigo_serial = forms.CharField(
        max_length=50,
        required=True,
        label="Código Serial",
        widget=forms.TextInput(attrs={'placeholder': 'Ej: TX-001'})
    )
    
    class Meta:
        model = RegistroCalibracion
        fields = '__all__'


class OrdenVibracionForm(forms.ModelForm):
    codigo_serial = forms.CharField(
        max_length=50,
        required=True,
        label="Código Serial",
        widget=forms.TextInput(attrs={'placeholder': 'Ej: BN-001'})
    )
    
    class Meta:
        model = OrdenVibracion
        fields = '__all__'


# ==========================================
# FUNCIÓN AUXILIAR PARA CONSTRUIR COMBOS
# ==========================================

def _construir_opciones_equipos_y_clientes():
    """
    Devuelve una lista de tuplas (valor, texto) para el combo de equipos.
    El valor es 'equipo|cliente|codigo_serial' y el texto es legible.
    """
    combinaciones = set()
    for reg in RegistroCalibracion.objects.all():
        combinaciones.add((reg.equipo, reg.cliente, reg.codigo_serial or ''))
    for ord_v in OrdenVibracion.objects.all():
        combinaciones.add((ord_v.equipo, ord_v.cliente, ord_v.codigo_serial or ''))
    
    mapa_equipos = {}
    for code, name in RegistroCalibracion.OPCIONES_EQUIPO_CALIBRACION:
        mapa_equipos[code] = name
    for code, name in OrdenVibracion.OPCIONES_EQUIPO_VIBRACION:
        mapa_equipos[code] = name
    
    mapa_clientes = {}
    for code, name in DiagnosticoPredictivo.OPCIONES_CLIENTE:
        mapa_clientes[code] = name
    
    opciones = []
    for equipo, cliente, serial in combinaciones:
        if equipo and cliente:
            nombre_equipo = mapa_equipos.get(equipo, equipo)
            nombre_cliente = mapa_clientes.get(cliente, cliente)
            serial_txt = f" (S/N: {serial})" if serial else ""
            valor = f"{equipo}|{cliente}|{serial}"
            texto = f"{nombre_equipo} - {nombre_cliente}{serial_txt}"
            opciones.append((valor, texto))
    
    opciones.sort(key=lambda x: x[1])
    return opciones


# ==========================================
# FORMULARIO DE DIAGNÓSTICO PREDICTIVO (CORREGIDO)
# ==========================================

class DiagnosticoPredictivoForm(forms.ModelForm):
    fecha_inicio = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'id': 'id_fecha_inicio'})
    )
    fecha_fin = forms.DateTimeField(
        required=True,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 'id': 'id_fecha_fin',
            'onchange': "var inicio = document.getElementById('id_fecha_inicio').value; if(inicio) { this.min = inicio; if(this.value && this.value < inicio) this.value = ''; }"
        })
    )

    class Meta:
        model = DiagnosticoPredictivo
        # 🔧 CORRECCIÓN: Agregar 'codigo_serial' a fields
        fields = ['equipo', 'codigo_serial', 'cliente', 'servicio', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'cliente': forms.Select(attrs={'id': 'id_cliente', 'style': 'pointer-events: none; background-color: #e9ecef;'}),
            'servicio': forms.Select(attrs={'id': 'id_servicio', 'style': 'pointer-events: none; background-color: #e9ecef;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        opciones = _construir_opciones_equipos_y_clientes()
        
        self.fields['equipo'] = forms.ChoiceField(
            choices=opciones, label="Equipo", required=True,
            widget=forms.Select(attrs={'id': 'id_equipo', 'onchange': 'actualizarClienteYServicio(this.value);'})
        )
        # Campo oculto para el código serial (se llena desde el JS)
        self.fields['codigo_serial'] = forms.CharField(
            required=False, widget=forms.HiddenInput(attrs={'id': 'id_codigo_serial'})
        )

        if self.instance and self.instance.fecha_inicio:
            self.fields['fecha_fin'].widget.attrs['min'] = self.instance.fecha_inicio.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        equipo_valor = cleaned_data.get("equipo")

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise forms.ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
        
        if equipo_valor:
            partes = equipo_valor.split('|')
            equipo = partes[0]
            cliente = partes[1] if len(partes) > 1 else None
            serial = partes[2] if len(partes) > 2 else None
            
            cleaned_data['equipo'] = equipo
            cleaned_data['codigo_serial'] = serial
            
            if cliente:
                registro = RegistroCalibracion.objects.filter(equipo=equipo, cliente=cliente, codigo_serial=serial).first()
                if registro:
                    cleaned_data['cliente'] = registro.cliente
                    cleaned_data['servicio'] = 'calibracion'
                    return cleaned_data
                orden = OrdenVibracion.objects.filter(equipo=equipo, cliente=cliente, codigo_serial=serial).first()
                if orden:
                    cleaned_data['cliente'] = orden.cliente
                    cleaned_data['servicio'] = 'vibracion'
                    return cleaned_data
            raise forms.ValidationError("No se encontró un registro válido para este equipo.")
        
        return cleaned_data


# ==========================================
# FORMULARIO DE REGISTRO DE INFORME (CORREGIDO)
# ==========================================

class RegistroInformeForm(forms.ModelForm):
    hora_inicio = forms.DateTimeField(
        label="Fecha y Hora de Inicio", required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 'id': 'id_hora_inicio',
            'onchange': "var fin = document.getElementById('id_hora_fin'); if(fin) { fin.min = this.value; if(fin.value && fin.value < this.value) fin.value = ''; }"
        })
    )
    hora_fin = forms.DateTimeField(
        label="Fecha y Hora de Fin", required=True,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 'id': 'id_hora_fin',
            'onchange': "var inicio = document.getElementById('id_hora_inicio').value; if(inicio) { this.min = inicio; if(this.value && this.value < inicio) this.value = ''; }"
        })
    )

    class Meta:
        model = RegistroInforme
        # 🔧 CORRECCIÓN: Agregar 'codigo_serial' a fields
        fields = ['titulo', 'equipo', 'codigo_serial', 'cliente', 'servicio', 'hora_inicio', 'hora_fin']
        widgets = {
            'cliente': forms.Select(attrs={'id': 'id_cliente_informe', 'style': 'pointer-events: none; background-color: #e9ecef;'}),
            'servicio': forms.Select(attrs={'id': 'id_servicio_informe', 'style': 'pointer-events: none; background-color: #e9ecef;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        opciones = _construir_opciones_equipos_y_clientes()
        
        self.fields['equipo'] = forms.ChoiceField(
            choices=opciones, label="Equipo", required=True,
            widget=forms.Select(attrs={'id': 'id_equipo_informe', 'onchange': 'actualizarClienteYServicioInforme(this.value); verificarDiagnostico(this.value);'})
        )
        self.fields['codigo_serial'] = forms.CharField(
            required=False, widget=forms.HiddenInput(attrs={'id': 'id_codigo_serial_informe'})
        )

        equipo_valor = None
        if self.instance and self.instance.equipo:
            equipo_valor = f"{self.instance.equipo}|{self.instance.cliente}|{self.instance.codigo_serial or ''}"
        elif self.data.get('equipo'):
            equipo_valor = self.data.get('equipo')
        
        if equipo_valor:
            partes = equipo_valor.split('|')
            equipo = partes[0]
            cliente = partes[1] if len(partes) > 1 else None
            serial = partes[2] if len(partes) > 2 else None
            
            qs = DiagnosticoPredictivo.objects.filter(equipo=equipo, fecha_fin__isnull=False)
            if cliente:
                qs = qs.filter(cliente=cliente)
            if serial:
                qs = qs.filter(codigo_serial=serial)
            ultimo_diagnostico = qs.order_by('-fecha_fin').first()
            
            if ultimo_diagnostico and ultimo_diagnostico.fecha_fin:
                self.fields['hora_inicio'].widget.attrs['min'] = ultimo_diagnostico.fecha_fin.strftime('%Y-%m-%dT%H:%M')
                self.fields['hora_inicio'].initial = ultimo_diagnostico.fecha_fin.strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get("hora_inicio")
        hora_fin = cleaned_data.get("hora_fin")
        equipo_valor = cleaned_data.get("equipo")

        if hora_inicio and hora_fin and hora_fin < hora_inicio:
            raise forms.ValidationError("La hora de fin no puede ser anterior a la hora de inicio.")
        
        if equipo_valor:
            partes = equipo_valor.split('|')
            equipo = partes[0]
            cliente = partes[1] if len(partes) > 1 else None
            serial = partes[2] if len(partes) > 2 else None
            
            cleaned_data['equipo'] = equipo
            cleaned_data['codigo_serial'] = serial
            
            qs = DiagnosticoPredictivo.objects.filter(equipo=equipo, fecha_fin__isnull=False)
            if cliente:
                qs = qs.filter(cliente=cliente)
            if serial:
                qs = qs.filter(codigo_serial=serial)
            ultimo_diagnostico = qs.order_by('-fecha_fin').first()
            
            if not ultimo_diagnostico:
                raise forms.ValidationError(
                    f"No existe un Diagnóstico Predictivo para este equipo (S/N: {serial or 'N/A'}). "
                    "Por favor, regístrelo primero en 'Diagnósticos Predictivos'."
                )
            
            if hora_inicio and ultimo_diagnostico.fecha_fin and hora_inicio < ultimo_diagnostico.fecha_fin:
                raise forms.ValidationError(
                    f"La hora de inicio del informe no puede ser anterior a la fecha de fin del diagnóstico ({ultimo_diagnostico.fecha_fin.strftime('%d/%m/%Y %H:%M')})."
                )
            
            if cliente:
                registro = RegistroCalibracion.objects.filter(equipo=equipo, cliente=cliente, codigo_serial=serial).first()
                if registro:
                    cleaned_data['cliente'] = registro.cliente
                    cleaned_data['servicio'] = 'calibracion'
                    return cleaned_data
                orden = OrdenVibracion.objects.filter(equipo=equipo, cliente=cliente, codigo_serial=serial).first()
                if orden:
                    cleaned_data['cliente'] = orden.cliente
                    cleaned_data['servicio'] = 'vibracion'
                    return cleaned_data
            raise forms.ValidationError("No se encontró un registro válido para este equipo.")
        
        return cleaned_data


# ==========================================
# FORMULARIO DE REGISTRO DE USUARIO
# ==========================================

class RegistroUsuarioForm(forms.Form):
    nombre_completo = forms.CharField(max_length=150, label="Nombre completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Rubén Pérez'}))
    email = forms.EmailField(label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}))
    telefono = forms.CharField(max_length=20, label="Número de teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+58 412 1234567'}))
    username = forms.CharField(max_length=150, label="Nombre de usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'usuario123'}))
    password1 = forms.CharField(label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'}))
    password2 = forms.CharField(label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '********'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso. Elige otro.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not re.match(r'^[\+\d\s\-]+$', telefono):
            raise ValidationError("El teléfono solo puede contener números, espacios, '+' y '-'.")
        if len(telefono.replace(' ', '').replace('-', '').replace('+', '')) < 7:
            raise ValidationError("El teléfono es demasiado corto.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        if password1 and len(password1) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return cleaned_data