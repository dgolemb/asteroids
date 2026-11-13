variable "location" {
  type    = string
  default = "westeurope"
}

variable "project_name" {
  type    = string
  default = "asteroids"
}

variable "resource_group_name" {
  type    = string
  default = "rg-AI-native-asteroids-training"
}

variable "managed_identity_name" {
  type    = string
  default = "ua-id-b213"
}

variable "acr_login_server" {
  type    = string
  default = "acrasteroids-f8gvczguabfzekb5.azurecr.io"
}

variable "docker_image" {
  type    = string
  default = "asteroids-web:latest"
}
