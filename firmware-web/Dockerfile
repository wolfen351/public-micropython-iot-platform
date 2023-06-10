FROM php:7.4.7-apache

COPY . /srv/app/public
RUN ls -la /srv/app/*

COPY config/vhost.conf /etc/apache2/sites-available/000-default.conf

RUN chown -R www-data:www-data /srv/app/public \
    && a2enmod rewrite
