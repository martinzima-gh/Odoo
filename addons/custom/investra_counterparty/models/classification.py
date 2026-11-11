from odoo import api, models

# Sektory ESA 2010, u kterých je reverzní repo pohledávkou za bankou (skupina 13 osnovy vyhlášky 501).
BANK_SECTORS = ("1210000", "1220000")


class InvestraPortfolioClassification(models.Model):
    _inherit = "investra.portfolio.classification"

    @api.model
    def _proposal_role(self, instrument, role, category, valid_from):
        """Reverzní repo s nebankovní protistranou je ve skupině 21 (rozhodnutí 2026-11-11). Bez protistrany nebo bez
        jejích údajů k datu zůstává návrh repo s bankou; skutečnou roli potvrzuje účetní."""
        role = super()._proposal_role(instrument, role, category, valid_from)
        if role != self.env.ref("investra_entity.role_repo") or not instrument.counterparty_id or not valid_from:
            return role
        profile = instrument.counterparty_id._counterparty_profile(valid_from)
        if profile and profile.sector_id.code not in BANK_SECTORS:
            return self.env.ref("investra_entity.role_repo_client")
        return role
