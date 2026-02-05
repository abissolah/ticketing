from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import (
    Prestataire,
    Client,
    ClientMember,
    Collaborateur,
    Ticket,
    TicketComment,
    TicketAttachment,
    InboundEmail,
)

User = get_user_model()


@admin.register(Prestataire)
class PrestataireAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ClientMemberInline(admin.TabularInline):
    model = ClientMember
    extra = 0
    fields = ("first_name", "last_name", "email", "color")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "prestataire", "user")
    list_filter = ("prestataire",)
    search_fields = ("name",)
    raw_id_fields = ("user",)
    inlines = [ClientMemberInline]
    autocomplete_fields = ("prestataire",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("prestataire", "user")


@admin.register(ClientMember)
class ClientMemberAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "client", "color_preview")
    list_filter = ("client",)
    search_fields = ("first_name", "last_name", "email")
    autocomplete_fields = ("client",)

    def color_preview(self, obj):
        return format_html(
            '<span style="background: {}; padding: 2px 12px; border-radius: 4px;">{}</span>',
            obj.color,
            obj.color,
        )

    color_preview.short_description = "Couleur"


@admin.register(Collaborateur)
class CollaborateurAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "prestataire",
        "function",
        "is_prestataire_admin",
        "user",
    )
    list_filter = ("prestataire", "is_prestataire_admin")
    search_fields = ("first_name", "last_name", "user__username")
    raw_id_fields = ("user",)
    filter_horizontal = ("clients",)
    autocomplete_fields = ("prestataire",)


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ("created_at",)
    raw_id_fields = ("author",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "client",
        "member",
        "priority",
        "status",
        "type",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "priority", "type", "client")
    search_fields = ("title", "description")
    raw_id_fields = ("created_by", "assigned_to")
    autocomplete_fields = ("client", "member")
    readonly_fields = ("created_at", "updated_at")
    inlines = [TicketCommentInline, TicketAttachmentInline]
    date_hierarchy = "created_at"


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    list_filter = ("ticket__client",)
    raw_id_fields = ("ticket", "author")
    readonly_fields = ("created_at",)


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ("name", "ticket", "comment", "uploaded_at")
    raw_id_fields = ("ticket", "comment")
    readonly_fields = ("uploaded_at",)


@admin.register(InboundEmail)
class InboundEmailAdmin(admin.ModelAdmin):
    list_display = ("from_email", "subject_short", "ticket", "received_at")
    list_filter = ("received_at",)
    search_fields = ("from_email", "subject", "message_id")
    readonly_fields = ("message_id", "from_email", "subject", "ticket", "received_at")
    raw_id_fields = ("ticket",)

    def subject_short(self, obj):
        return (obj.subject or "")[:60] + ("..." if len(obj.subject or "") > 60 else "")

    subject_short.short_description = "Sujet"
