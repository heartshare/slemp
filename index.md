---
layout: default
---

<section id="features"></section>

## Apa itu SLEMP?

### Penjelasan Singkat
Simple, Linux, Engine-X (Nginx via Opensresty), MySQL, PHP-FPM. Panel web sederhana untuk Centos Linux. Berisi perangkat lunak untuk kebutuhan server web yang dipasang dan dikonfigurasikan dari kode sumbernya (bukan paket bawaan distro). Terima kasih kepada BT.CN karena telah menulis perangkat lunak manajemen web yang begitu bagus. Setelah saya melihatnya, saya tahu ini adalah manajemen server berbasis web yang selalu saya inginkan. Saya menyalin antarmuka manajemennya dan menulis versi sesuai kebutuhan saya.

### Plugin-plugin utama
* OpenResty[1.13-1.19] - Lightweight, occupies less memory, and has strong concurrency capabilities.
* PHP[5.2-8.1] - PHP is the best programming language in the world.
* MySQL[5.5-8.0] - MySQL is a relational database management system.
* phpMyAdmin - The famous Web-side MySQL management tool.
* PM2 - Manager & built-in node.js + npm + nvm + pm2

### Fitur-Fitur
* Pengoptimalan akses SSH
* Fitur-fitur sebuan panel server yang lengkap
* Website subdirectory binding
* Fitur backup website dan database
* Update otomatis
* Manajemen Plugins
* Informasi Sistem (Server)
* Site Manager
* Free SSL
* File Manager
* Database Manager
* Monitor CPU, Jaringan, Baca tulis Disk, Memory (RAM)
* Firewall dan pencatatan keamanan
* Crontab Manager
* Replika Database (Master-Slave)
* Sinkronisasi File (Rsync Lokal atau Remote)
* Backup ke Google Drive

Pada dasarnya SLEMP Panel bisa digunakan dan akan terus dioptimalkan kedepannya! Fork dan komentar dipersilakan!

<section id="install"></section>

## Bagaimana cara pasang SLEMP?
### Persyaratan sistem
* Memori: 128M atau lebih, disarankan 512M atau lebih
* Disk: Setidaknya 4GB ruang disk kosong
* Lainnya: Pastikan itu adalah sistem operasi yang bersih, tidak ada Apache / Nginx / PHP / MySQL / MariaDB yang diinstal sebelumnya.

### Perintah Pemasangan
```
curl -fsSL https://raw.githubusercontent.com/basoro/slemp/main/scripts/install.sh | sh
```

### Perintah Pembaruan

```
curl -fsSL https://raw.githubusercontent.com/basoro/slemp/main/scripts/update.sh | sh
```

<section id="screenshot"></section>

## Tangkapan layar SLEMP

<div class="slideshow-container">

<div class="mySlides fade">
  <img src="https://raw.githubusercontent.com/basoro/slemp/main/docs/slemp.png" style="width:100%">
  <div class="text">Dashboard</div>
</div>

<div class="mySlides fade">
  <img src="https://raw.githubusercontent.com/basoro/slemp/main/docs/monitor.png" style="width:100%">
  <div class="text">Moniter Server</div>
</div>

<div class="mySlides fade">
  <img src="https://raw.githubusercontent.com/basoro/slemp/main/docs/firewall.png" style="width:100%">
  <div class="text">Pengaturan Firewall</div>
</div>

</div>
<br>

<div style="text-align:center">
  <span class="dot"></span>
  <span class="dot"></span>
  <span class="dot"></span>
</div>

## Umpan Balik dan Bantuan
