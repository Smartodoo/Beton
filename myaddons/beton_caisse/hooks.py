BANK_METHOD_CODES = ('beton_cheque', 'beton_virement', 'beton_carte')
CASH_METHOD_CODES = ('beton_especes',)


def sync_beton_payment_method_lines(env):
    """Garantit que les modes de paiement béton sont rattachés uniquement aux
    journaux du bon type :
      - beton_cheque / beton_virement / beton_carte  -> journaux 'bank' uniquement
      - beton_especes                                -> journaux 'cash' uniquement
    Supprime les rattachements erronés et crée les manquants.
    """
    Line = env['account.payment.method.line']

    # 1) Suppression des lignes mal rattachées
    wrong_lines = Line.search([
        '|',
        '&', ('payment_method_id.code', 'in', BANK_METHOD_CODES),
             ('journal_id.type', '!=', 'bank'),
        '&', ('payment_method_id.code', 'in', CASH_METHOD_CODES),
             ('journal_id.type', '!=', 'cash'),
    ])
    if wrong_lines:
        wrong_lines.sudo().unlink()

    # 2) Création des lignes manquantes sur les journaux du bon type
    methods = env['account.payment.method'].search([
        ('code', 'in', BANK_METHOD_CODES + CASH_METHOD_CODES),
    ])
    for method in methods:
        target_type = 'bank' if method.code in BANK_METHOD_CODES else 'cash'
        journals = env['account.journal'].search([
            ('type', '=', target_type),
            ('company_id', 'in', env.companies.ids),
        ])
        for journal in journals:
            existing = Line.search([
                ('payment_method_id', '=', method.id),
                ('journal_id', '=', journal.id),
            ], limit=1)
            if not existing:
                Line.sudo().create({
                    'name': method.name,
                    'payment_method_id': method.id,
                    'journal_id': journal.id,
                })


def post_init_hook(env):
    sync_beton_payment_method_lines(env)
