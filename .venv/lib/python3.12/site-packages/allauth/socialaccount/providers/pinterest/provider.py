from __future__ import annotations

from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.pinterest.views import PinterestOAuth2Adapter


class PinterestAccount(ProviderAccount):
    def get_username(self):
        return self.account.extra_data.get("username")

    def get_profile_url(self):
        username = self.get_username()
        if username:
            return f"https://www.pinterest.com/{username}/"
        return None

    def get_avatar_url(self):
        return self.account.extra_data.get("profile_image")


class PinterestProvider(OAuth2Provider):
    id = "pinterest"
    name = "Pinterest"
    account_class = PinterestAccount
    oauth2_adapter_class = PinterestOAuth2Adapter

    def get_default_scope(self):
        # See: https://developers.pinterest.com/docs/getting-started/scopes/
        return ["user_accounts:read"]

    def extract_extra_data(self, data):
        return data

    def extract_uid(self, data):
        return data["id"]

    def extract_common_fields(self, data):
        return dict(username=data["username"])


provider_classes = [PinterestProvider]
