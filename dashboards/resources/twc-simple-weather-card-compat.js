customElements.whenDefined("simple-weather-card").then(() => {
  const SimpleWeatherCard = customElements.get("simple-weather-card");

  if (!SimpleWeatherCard || SimpleWeatherCard.prototype.__twcCompatApplied) {
    return;
  }

  SimpleWeatherCard.prototype.toLocale = function toLocale(key, fallback = "unknown") {
    const language = this.hass?.selectedLanguage || this.hass?.language;
    const resources = this.hass?.resources;
    const translated = language ? resources?.[language]?.[key] : undefined;

    return translated || this.hass?.localize?.(key) || fallback;
  };

  SimpleWeatherCard.prototype.__twcCompatApplied = true;
});
