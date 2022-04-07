from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from aifinder import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token

# Create your views here.
def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request, "Usuario ja existente, tente outro usuario.")
            return redirect('home')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email ja registrado!")
            return redirect('home')
        
        if len(username)>20:
            messages.error(request, "Usuario precisa ser com menos de 20 caracteres!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "As senhas nao se coincidem!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Usuario precisa ser alfa-numerico!")
            return redirect('home')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()
        messages.success(request, "Sua conta foi criada! Cheque seu e-mail para confirmar sua identidade e ativar sua conta!.")
        
        # Email de boas vindas
        subject = "Seja bem vindo ao Ai-Finder!"
        message = "Ola " + myuser.first_name + "!! \n" + "bem vindo ao Ai-Finder \nobrigado por visitar nosso site\n. Enviamos um e-mail de confimacao, cheque sua caixa de mensagem. \n\nObrigado, \nAi-Finder Company"        
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        # Confirmacao de email
        current_site = get_current_site(request)
        email_subject = "Confime seu e-mail para prosseguir no Ai-Finder!"
        message2 = render_to_string('email_confirmation.html',{
            
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
        email_subject,
        message2,
        settings.EMAIL_HOST_USER,
        [myuser.email],
        )
        email.fail_silently = True
        email.send()
        
        return redirect('signin')
        
        
    return render(request, "authentication/signup.html")


def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request,myuser)
        messages.success(request, "Sua conta foi criada com sucesso!")
        return redirect('signin')
    else:
        return render(request,'activation_failed.html')


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            fname = user.first_name
            # messages.success(request, "Logado com sucesso!")
            return render(request, "authentication/index.html",{"fname":fname})
        else:
            messages.error(request, "Credenciais erradas!")
            return redirect('home')
    
    return render(request, "authentication/signin.html")


def signout(request):
    logout(request)
    messages.success(request, "Deslogado com sucesso!")
    return redirect('home')