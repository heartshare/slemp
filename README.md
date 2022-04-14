### SLEMP Panel
Simple, Linux, Engine-X (Nginx via Opensresty), MySQL, PHP-FPM. Panel web sederhana untuk Centos Linux. Berisi perangkat lunak untuk kebutuhan server web yang dipasang dan dikonfigurasikan dari kode sumbernya (bukan paket bawaan distro). Terima kasih kepada BT.CN karena telah menulis perangkat lunak manajemen web yang begitu bagus. Setelah saya melihatnya, saya tahu ini adalah manajemen server berbasis web yang selalu saya inginkan. Saya menyalin antarmuka manajemennya dan menulis versi sesuai kebutuhan saya.


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


### Plugin-plugin utama
* OpenResty[1.13-1.19] - Lightweight, occupies less memory, and has strong concurrency capabilities.
* PHP[5.2-8.1] - PHP is the best programming language in the world.
* MySQL[5.5-8.0] - MySQL is a relational database management system.
* phpMyAdmin - The famous Web-side MySQL management tool.
* PM2 - Manager & built-in node.js + npm + nvm + pm2

### Pemasangan
```
curl -fsSL  https://raw.githubusercontent.com/basoro/slemp/master/scripts/install.sh | sh
```

### Pembaruan

```
curl -fsSL  https://raw.githubusercontent.com/basoro/slemp/master/scripts/update.sh | sh
```

### Wiki
[More info...](https://github.com/basoro/slemp/wiki)
