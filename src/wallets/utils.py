def get_wallet_pk(request):
    return request.parser_context.get("kwargs", {}).get("wallet_pk")
