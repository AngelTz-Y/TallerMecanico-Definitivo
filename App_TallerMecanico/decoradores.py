# decoradores.py
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Registro

# Mapeo de roles a sus vistas de inicio correspondientes
ROLE_REDIRECTS = {
    "admin": "admin_panel",
    "mecanico": "dashboard_mecanico",
    "cliente": "cliente_panel",
}

def role_required(*roles):
    """
    Decorador para verificar el rol del usuario antes de acceder a la vista.
    Redirige al usuario a una página de error si no tiene permisos, desde donde
    puede regresar a su panel principal.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_id = request.session.get('user_id')
            if user_id:
                user = Registro.objects.filter(id=user_id).first()
                if user and user.role in roles:
                    return view_func(request, *args, **kwargs)
                else:
                    # Mensaje de error y redirección a la página de permiso
                    if user:
                        messages.error(request, "Tú no tienes permiso de estar aquí.")
                        # Pasar el rol del usuario al contexto para la redirección en la plantilla
                        return render(request, "mensajePermiso.html", {
                            "redirect_url": ROLE_REDIRECTS.get(user.role, "inicio"),
                            "user_role": user.role
                        })
                    else:
                        messages.error(request, "Inicia sesión para continuar.")
                        return redirect("login")
            else:
                messages.error(request, "Inicia sesión para continuar.")
                return redirect("login")
        return wrapper
    return decorator
