// Magic & Blocks wiki (site estatico: funciona direto no GitHub Pages ou abrindo o arquivo no navegador).
// Busca da barra lateral: filtra a lista e as entradas da pagina pelo nome.
// Destaca na lista a entrada que esta visivel na tela.
(function () {
  var input = document.getElementById('busca');
  var links = Array.prototype.slice.call(document.querySelectorAll('.side-list a'));
  var entries = Array.prototype.slice.call(document.querySelectorAll('.entry'));
  if (!input) return;

  function norm(s) {
    return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  input.addEventListener('input', function () {
    var q = norm(input.value.trim());
    entries.forEach(function (e, i) {
      var show = !q || norm(e.getAttribute('data-name')).indexOf(q) >= 0 || norm(e.textContent).indexOf(q) >= 0;
      e.style.display = show ? '' : 'none';
      if (links[i]) links[i].style.display = show ? '' : 'none';
    });
  });

  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (items) {
      items.forEach(function (it) {
        if (!it.isIntersecting) return;
        links.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + it.target.id); });
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    entries.forEach(function (e) { obs.observe(e); });
  }
})();
