import frappe

def get_context(context):
    # This allows viewing recent error logs
    context.no_cache = 1
    return context
