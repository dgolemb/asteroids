export ARM_CLIENT_ID=$(security find-generic-password -a "$USER" -s asteroids-arm-client-id -w)
export ARM_CLIENT_SECRET=$(security find-generic-password -a "$USER" -s asteroids-arm-client-secret -w)
export ARM_TENANT_ID=$(security find-generic-password -a "$USER" -s asteroids-arm-tenant-id -w)
export ARM_SUBSCRIPTION_ID=$(security find-generic-password -a "$USER" -s asteroids-arm-subscription-id -w)
