# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AccountEmailaddress(models.Model):
    email = models.CharField(max_length=254)
    verified = models.IntegerField()
    primary = models.IntegerField()
    user = models.ForeignKey('Usuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'
        unique_together = (('user', 'email'),)


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AppointmentsScheduledworkday(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateField(unique=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_working = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'appointments_scheduledworkday'


class AppointmentsWorkscheduletemplate(models.Model):
    id = models.BigAutoField(primary_key=True)
    day_of_week = models.IntegerField(unique=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_working_day = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'appointments_workscheduletemplate'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class CategoriaServicio(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'categoria_servicio'


class Citas(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField()
    status = models.CharField(max_length=20)
    notes = models.TextField()
    client = models.ForeignKey('Usuario', models.DO_NOTHING)
    service = models.ForeignKey('Servicio', models.DO_NOTHING)
    appointment_date = models.DateField(blank=True, null=True)
    appointment_time = models.TimeField(blank=True, null=True)
    staff = models.ForeignKey('Usuario', models.DO_NOTHING, related_name='citas_staff_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'citas'


class ClientsClientprofile(models.Model):
    id = models.BigAutoField(primary_key=True)
    client_type = models.CharField(max_length=20)
    user = models.OneToOneField('Usuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'clients_clientprofile'


class Cotizacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    quotation_number = models.CharField(unique=True, max_length=20)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    valid_until = models.DateField()
    status = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField()
    appointment = models.OneToOneField(Citas, models.DO_NOTHING, blank=True, null=True)
    client = models.ForeignKey('Usuario', models.DO_NOTHING)
    staff = models.ForeignKey('Usuario', models.DO_NOTHING, related_name='cotizacion_staff_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cotizacion'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Usuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoPlotlyDashDashapp(models.Model):
    instance_name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=110)
    base_state = models.TextField()
    creation = models.DateTimeField()
    update = models.DateTimeField()
    save_on_change = models.IntegerField()
    stateless_app = models.ForeignKey('DjangoPlotlyDashStatelessapp', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_plotly_dash_dashapp'


class DjangoPlotlyDashStatelessapp(models.Model):
    app_name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=110)

    class Meta:
        managed = False
        db_table = 'django_plotly_dash_statelessapp'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class ItemCotizacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    item_type = models.CharField(max_length=10)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    product = models.ForeignKey('Producto', models.DO_NOTHING, blank=True, null=True)
    quotation = models.ForeignKey(Cotizacion, models.DO_NOTHING)
    service = models.ForeignKey('Servicio', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item_cotizacion'


class Producto(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    is_active = models.IntegerField()
    category = models.ForeignKey(CategoriaServicio, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'producto'


class ServicesServiceimage(models.Model):
    id = models.BigAutoField(primary_key=True)
    image = models.CharField(max_length=100, blank=True, null=True)
    is_featured = models.IntegerField()
    service = models.ForeignKey('Servicio', models.DO_NOTHING)
    image_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'services_serviceimage'


class ServicesServicevideo(models.Model):
    id = models.BigAutoField(primary_key=True)
    video = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200)
    service = models.ForeignKey('Servicio', models.DO_NOTHING)
    video_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'services_servicevideo'


class Servicio(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    category = models.ForeignKey(CategoriaServicio, models.DO_NOTHING)
    slug = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'servicio'


class SiteConfigCarouselimage(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200)
    image = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField()
    active = models.IntegerField()
    button_text = models.CharField(max_length=50)
    button_url = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'site_config_carouselimage'


class SiteConfigSiteimage(models.Model):
    id = models.BigAutoField(primary_key=True)
    location = models.CharField(unique=True, max_length=50)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.CharField(max_length=100)
    bio = models.TextField()
    instagram_url = models.CharField(max_length=200)
    linkedin_url = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'site_config_siteimage'


class SiteConfigSitesettings(models.Model):
    id = models.BigAutoField(primary_key=True)
    site_name = models.CharField(max_length=100)
    logo = models.CharField(max_length=100)
    favicon = models.CharField(max_length=100, blank=True, null=True)
    footer_text = models.TextField()
    facebook_url = models.CharField(max_length=200)
    instagram_url = models.CharField(max_length=200)
    whatsapp_number = models.CharField(max_length=20)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=254)

    class Meta:
        managed = False
        db_table = 'site_config_sitesettings'


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=200)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.JSONField()
    user = models.ForeignKey('Usuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)
    provider_id = models.CharField(max_length=200)
    settings = models.JSONField()

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    id = models.BigAutoField(primary_key=True)
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class Usuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    dni = models.CharField(max_length=20)
    is_verified = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'usuario'


class UsuarioGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Usuario, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuario_groups'
        unique_together = (('user', 'group'),)


class UsuarioUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Usuario, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuario_user_permissions'
        unique_together = (('user', 'permission'),)
