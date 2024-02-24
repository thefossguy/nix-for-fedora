## START: Set by rpmautospec
## (rpmautospec version 0.3.5)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 2;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

Name:           nix
Version:        2.18.1
Release:        %autorelease
Summary:        Package manager for NixOS

License:        LGPL-2.1
URL:            https://github.com/NixOS/nix
Source0:        https://github.com/NixOS/nix/archive/%{version_no_tilde}/%{name}-%{version_no_tilde}.tar.gz

BuildRequires:  autoconf
BuildRequires:  autoconf-archive
BuildRequires:  automake
BuildRequires:  boost-devel
BuildRequires:  brotli-devel
BuildRequires:  curl-devel
BuildRequires:  editline-devel
BuildRequires:  gc-devel
BuildRequires:  json-devel
BuildRequires:  libarchive-devel
BuildRequires:  libcpuid-devel
BuildRequires:  libseccomp-devel
BuildRequires:  libsodium-devel
BuildRequires:  lowdown-devel
BuildRequires:  openssl-devel
BuildRequires:  sqlite-devel
BuildRequires:  gcc-c++
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  systemd-rpm-macros
BuildRequires:  jq
# For documentation, not yet used:
# BuildRequires:  graphviz

%description
Nix is a purely functional package manager. This means that it treats packages
like values in purely functional programming languages such as Haskell — they
are built by functions that don’t have side-effects, and they never change after
they have been built. Nix stores packages in the Nix store, usually the
directory /nix/store, where each package has its own unique subdirectory.

%prep
%autosetup

%build
autoreconf -vfi

OPTIONS=(
  # We need to disable tests because 'rapidtest' dependency is missing
  --disable-tests

  # Documentation is available online
  --disable-doc-gen

  # Those libraries are unversioned, and we don't install the headers,
  # so let's move them out of the public dir.
  --libdir=%{_libdir}/nix
  --libexecdir=%{_libexecdir}
)

%configure "${OPTIONS[@]}"
%make_build

%install
%make_install

# Devel files that we don't want to use
rm -r %{buildroot}%{_includedir}/nix \
      %{buildroot}%{_libdir}/nix/pkgconfig

# Duplicate shell completion files
rm -r %{buildroot}/etc/profile.d

rm %{buildroot}/etc/init/nix-daemon.conf

ln -vfs --relative %{buildroot}$(readlink %{buildroot}%{_libexecdir}/nix/build-remote) \
                                          %{buildroot}%{_libexecdir}/nix/build-remote

%post
%systemd_post nix-daemon.socket nix-daemon.service

%preun
%systemd_preun nix-daemon.socket nix-daemon.service

%postun
%systemd_postun_with_restart nix-daemon.socket nix-daemon.service

%files
%{_bindir}/nix
%{_bindir}/nix-*
%dir %{_libdir}/nix
%{_libdir}/nix/libnix*.so
%{_libexecdir}/nix/build-remote
%{_datadir}/bash-completion/completions/nix
%{_datadir}/fish/vendor_completions.d/nix.fish
%{_datadir}/zsh/site-functions/*nix
%doc README.md
%license COPYING

# Let's ignore the daemon stuff for now
%_unitdir/nix-daemon.socket
%_unitdir/nix-daemon.service
%_tmpfilesdir/nix-daemon.conf

%changelog
* Tue Nov 07 2023 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 2.18.1-2
- Switch to already-packaged json dependency and add service files

* Wed Nov 01 2023 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 2.18.1-1
- Initial packaging
