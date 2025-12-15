from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # -----------------------------
    # DASHBOARD
    # -----------------------------
    path('', views.dashboard, name='dashboard'),
    path('<int:school_id>/', views.transaction_list, name='transaction_list'),
    path('<int:school_id>/create/', views.transaction_create, name='transaction_create'),
    path('update/<int:pk>/', views.transaction_update, name='transaction_update'),
    path('delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),

    path("student/", views.student_dashboard, name="student_dashboard"),

    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoice/create/", views.invoice_create, name="invoice_create"),
    path("invoice/<int:pk>/update/", views.invoice_update, name="invoice_update"),
    path("invoice/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("", views.generate_invoices, name="generate_invoices"),
    path("invoice/delete/<int:pk>/", views.invoice_delete, name="invoice_delete"),


    path("payment/record/", views.record_payment, name="record_payment"),

    path("expenses/", views.expense_list, name="expense_list"),
    path("expense/create/", views.expense_create, name="expense_create"),

    path("summary/json/", views.finance_summary_json, name="finance_summary_json"),
    path("invoice/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("receipt/<int:pk>/pdf/", views.receipt_pdf, name="receipt_pdf"),
    path("invoice/bulk-create/", views.bulk_generate_invoices, name="bulk_invoice_create"),

    path("receipt/<int:payment_id>/", views.payment_receipt, name="payment_receipt"),

    path("reports/", views.financial_reports, name="financial_reports"),

    path("student/<int:student_id>/payments/", views.student_payments, name="student_payments"),
    
    path("payment/edit/<int:pk>/", views.payment_edit, name="payment_edit"),
    path("payment/reverse/<int:pk>/", views.payment_reverse, name="payment_reverse"),

    path("invoice/<int:invoice_id>/payments/", views.invoice_payments_json, name="invoice_payments_json"),



    
]
