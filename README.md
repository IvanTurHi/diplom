# Диплом  
Адрес сайта -- http://127.0.0.1  
Документация разработчика -- https://docs.google.com/document/d/1o8ec3pxBQlVCKecnff_QwnTyEFX4FqVJ/edit?usp=sharing&ouid=100138284540665406355&rtpof=true&sd=true  
Документация пользователя -- https://docs.google.com/document/d/16xOFhFcKUq8P0S96vTB_5IMkH341thrO/edit?usp=sharing&ouid=100138284540665406355&rtpof=true&sd=true  
  
<h2>Инструкция по локальному развертыванию</h2>
<ol>
<li>Скачать docker согласно своей ОС:
<ul>
  <li>Windows: https://learn.microsoft.com/ru-ru/virtualization/windowscontainers/manage-docker/configure-docker-daemon
  <li>Linux Ubuntu 18.04: https://www.digitalocean.com/community/tutorials/docker-ubuntu-18-04-1-ru
  <li>Linux Ubuntu 20.04: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04
  <li>Linux Ubuntu 22.04: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
  <li>Other: В таком случае, я думаю, вы продвинутый пользователь и инструкция Вам не нужна
 </ul>
<li>Скачать ветку local данного репозитория
<li>Перейти в папку docker_local
<li>В случае необходимости подредактировать файл ".env":
<li>Убедиться, что docker server запущен
<li>Запустить команду docker-compose up
<li>Вы замечательны
<li>Не забыть после использования погасить стенд docker-compose down
</ol>

<h2>Дополнительные возможности</h2>
В файле 'отладочные контейнеры.txt' лежат заготовки для вспомогательных контейнеров pgadmin и mongo-express, позволяющие напрямую обращаться к СУБД. Их можно использовать как угодно
