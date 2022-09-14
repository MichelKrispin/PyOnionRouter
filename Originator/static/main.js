// =======================
// Initialization
// =======================

const animateRouter = (route, result, speed) => {
  // =======================
  // Functions
  // =======================

  const editRect = (rect, fill, stroke, linewidth) => {
    rect.fill = fill;
    rect.stroke = stroke;
    rect.linewidth = linewidth;
  };

  const createBox = (title, x, y, borderColor, stretch = 1, stretchY = 1) => {
    let rect = two.makeRoundedRectangle(
      x,
      y,
      boxW * stretch,
      boxH * stretch * stretchY,
      5
    );
    editRect(rect, '#FFF', borderColor, 5);
    two.makeText(title, x, y, { family: fontFamily, weight: 800 });
  };

  const base = () => {
    // Create the client box
    createBox('Client', clientPos.x, clientPos.y, '#1C75BC');

    // Create the directory box
    createBox('Directory', directoryPos.x, directoryPos.y, '#751CBC');

    // Create the nodes
    createBox(`${route[0]}`, nodeX, node1Y, '#BC751C', 3, 0.5);
    createBox(`${route[1]}`, nodeX, node2Y, '#BC751C', 3, 0.5);
    createBox(`${route[2]}`, nodeX, node3Y, '#BC751C', 3, 0.5);

    // Create the service box
    createBox('Service', servicePos.x, servicePos.y, '#1CBC75');
  };

  const makeText = (text, x, y) => {
    let textBox = two.makeText(text, x, y, { family: fontFamily });
    let bounding = textBox.getBoundingClientRect();
    let rect = two.makeRectangle(
      x,
      y,
      bounding.right - bounding.left,
      bounding.bottom - bounding.top
    );
    editRect(rect, '#FFF', '#FFF', 0);
    textBox.remove();
    textBox = two.makeText(text, x, y, { family: fontFamily });
  };

  /**
   * Animate the package from start to end.
   * @param {int} layers
   * @param {int} startX
   * @param {int} startY
   * @param {int} endX
   * @param {int} endY
   */
  const animatePackage = (
    layers,
    startX,
    startY,
    endX,
    endY,
    request = true
  ) => {
    let elements = drawPackage(layers, startX, startY, request);
    let groupedPackage = two.makeGroup(elements);

    // Move with 60 fps
    const maxFrame = (timeDiff / 1000) * 60;
    let first = -1;
    two.bind('update', (frameCount) => {
      if (first === -1) {
        first = frameCount;
      }
      const frame = frameCount - first;
      if (frame > maxFrame) {
        first = -1;
        two.pause();
        two.unbind(this);
      }
      const alpha = frame / maxFrame;
      groupedPackage.position.set(
        alpha * (endX - startX),
        alpha * (endY - startY)
      );
    });
    two.play();
  };

  /**
   * Draw the package boxes with the specified number of layers.
   * @param {int} layers
   * @param {int} x
   * @param {int} y
   */
  const drawPackage = (layers, x, y, request = true) => {
    let elems = [];
    if (layers > 3) {
      let w = boxW;
      let h = boxH * 2.1;
      let inner = two.makeRoundedRectangle(x, y - h / 4, w, h, 5);
      editRect(inner, '#FFF', 'blue', 2);
      let text = two.makeText(request ? '#1' : '#Client', x, y - h / 1.5, {
        family: fontFamily,
      });
      elems.push(inner);
      elems.push(text);
    }

    if (layers > 2) {
      let w = boxW * 0.9;
      let h = boxH * 1.7;
      let inner = two.makeRoundedRectangle(x, y - h / 4.5, w, h, 5);
      editRect(inner, '#FFF', 'blue', 2);
      let text = two.makeText(request ? '#2' : '#Client', x, y - h / 1.75, {
        family: fontFamily,
      });
      elems.push(inner);
      elems.push(text);
    }

    if (layers > 1) {
      let w = boxW * 0.8;
      let h = boxH * 1.25;
      let inner = two.makeRoundedRectangle(x, y - h / 6, w, h, 5);
      editRect(inner, '#FFF', 'blue', 2);
      let text = two.makeText(request ? '#3' : '#Client', x, y - h / 2, {
        family: fontFamily,
      });
      elems.push(inner);
      elems.push(text);
    }

    let package = two.makeRoundedRectangle(x, y, boxW * 0.71, boxH * 0.7, 5);
    editRect(package, '#FFF', 'blue', 2);
    let text = two.makeText(request ? 'Request' : 'Response', x, y, {
      family: fontFamily,
    });
    elems.push(package);
    elems.push(text);
    return elems;
  };

  /**
   * Draw the next part of the animation
   * @param {function} f The drawing function
   * @param {int} p The pause until the function is called
   * @returns
   */
  const drawNext = (f, p) => {
    setTimeout(function () {
      two.clear();
      f();
      base();
      two.update();
    }, p);
    return p + timeDiff;
  };

  // =======================
  // Global constants
  // =======================

  let dashboard = document.getElementById('dashboard');
  const width = dashboard.offsetWidth;
  const height = 600;

  const fontFamily = 'Helvetica';
  const clientPos = { x: width * 0.1, y: height * 0.2 };
  const directoryPos = { x: width * 0.5, y: height * 0.1 };
  const servicePos = { x: clientPos.x, y: height * 0.9 };
  const nodeX = width * 0.8;
  const node1Y = height * 0.3;
  const node2Y = height * 0.5;
  const node3Y = height * 0.7;
  const boxW = 100;
  const boxH = 50;
  const boxWhalf = boxW / 2;
  const boxHhalf = boxH / 2;
  let pause = 0; //1000;
  const timeDiff = speed * 1000; // 250;

  // =======================
  // Drawing
  // =======================

  dashboard.innerHTML = '';
  let two = new Two({
    width: width,
    height: height,
  }).appendTo(dashboard);

  // Start
  base();
  two.update();

  // Route request
  pause = drawNext(() => {
    two.makeArrow(
      clientPos.x + boxWhalf,
      clientPos.y - boxHhalf,
      directoryPos.x - boxWhalf,
      directoryPos.y + boxHhalf
    );
    makeText(
      'GET /route',
      clientPos.x + (directoryPos.x - clientPos.x) / 2,
      clientPos.y + (directoryPos.y - clientPos.y) / 2
    );
  }, pause + 3 * timeDiff);

  // Return route
  pause = drawNext(() => {
    two.makeArrow(
      directoryPos.x - boxWhalf,
      directoryPos.y + boxHhalf,
      clientPos.x + boxWhalf,
      clientPos.y - boxHhalf
    );
    makeText(
      // '[8000] -> [8001] -> [8002]',
      '[' + route.join('] -> [') + ']',
      clientPos.x + (directoryPos.x - clientPos.x) / 2,
      clientPos.y + (directoryPos.y - clientPos.y) / 2
    );
  }, pause + 3 * timeDiff);

  // Package wrapping
  pause = drawNext(() => {
    drawPackage(1, clientPos.x, clientPos.y + 3 * boxH);
  }, pause + 3 * timeDiff);

  pause = drawNext(() => {
    drawPackage(2, clientPos.x, clientPos.y + 3 * boxH);
  }, pause);

  pause = drawNext(() => {
    drawPackage(3, clientPos.x, clientPos.y + 3 * boxH);
  }, pause);

  pause = drawNext(() => {
    drawPackage(4, clientPos.x, clientPos.y + 3 * boxH);
  }, pause);

  // Move wrapped package to first node
  const packageX = nodeX - 3 * boxW;
  const packageY = (ny) => {
    return ny + boxH / 2;
  };

  pause = drawNext(() => {
    animatePackage(
      4,
      clientPos.x,
      clientPos.y + 3 * boxH,
      packageX,
      packageY(node1Y)
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(4, packageX, packageY(node1Y));
  }, pause);

  // Unwrap first layer
  pause = drawNext(() => {
    drawPackage(3, packageX, packageY(node1Y));
  }, pause);

  // Move to second node
  pause = drawNext(() => {
    animatePackage(3, packageX, packageY(node1Y), packageX, packageY(node2Y));
  }, pause);
  pause = drawNext(() => {
    drawPackage(3, packageX, packageY(node2Y));
  }, pause);

  // Unwrap second layer
  pause = drawNext(() => {
    drawPackage(2, packageX, packageY(node2Y));
  }, pause);

  // Move to third node
  pause = drawNext(() => {
    animatePackage(
      2,
      packageX,
      packageY(node2Y),
      packageX,
      packageY(node3Y - boxHhalf)
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(2, packageX, packageY(node3Y - boxHhalf));
  }, pause);

  // Unwrap last layer
  pause = drawNext(() => {
    drawPackage(1, packageX, packageY(node3Y - boxHhalf));
  }, pause);

  // Move to service
  pause = drawNext(() => {
    animatePackage(
      1,
      packageX,
      packageY(node3Y - boxHhalf),
      servicePos.x,
      servicePos.y - boxH
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(1, servicePos.x, servicePos.y - boxH);
  }, pause);

  // --> Received

  // Swap to response
  pause = drawNext(() => {
    drawPackage(1, servicePos.x, servicePos.y - boxH, false);
  }, pause);

  // Send the whole route back
  // Move to third node
  pause = drawNext(() => {
    animatePackage(
      1,
      servicePos.x,
      servicePos.y - boxH,
      packageX,
      packageY(node3Y - boxHhalf),
      false
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(1, packageX, packageY(node3Y - boxHhalf), false);
  }, pause);

  // Wrap at last layer
  pause = drawNext(() => {
    drawPackage(2, packageX, packageY(node3Y - boxHhalf), false);
  }, pause);

  // Move to second node
  pause = drawNext(() => {
    animatePackage(
      2,
      packageX,
      packageY(node3Y - boxHhalf),
      packageX,
      packageY(node2Y),
      false
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(2, packageX, packageY(node2Y), false);
  }, pause);

  // Wrap at second layer
  pause = drawNext(() => {
    drawPackage(3, packageX, packageY(node2Y), false);
  }, pause);

  // Move to first node
  pause = drawNext(() => {
    animatePackage(
      3,
      packageX,
      packageY(node2Y),
      packageX,
      packageY(node1Y),
      false
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(3, packageX, packageY(node1Y), false);
  }, pause);

  // Wrap at second layer
  pause = drawNext(() => {
    drawPackage(4, packageX, packageY(node1Y), false);
  }, pause);

  // Move to client
  pause = drawNext(() => {
    animatePackage(
      4,
      packageX,
      packageY(node1Y),
      clientPos.x,
      clientPos.y + 3 * boxH,
      false
    );
  }, pause);
  pause = drawNext(() => {
    drawPackage(4, clientPos.x, clientPos.y + 3 * boxH, false);
  }, pause);

  // Unwrap three times at client
  pause = drawNext(() => {
    drawPackage(3, clientPos.x, clientPos.y + 3 * boxH, false);
  }, pause);
  pause = drawNext(() => {
    drawPackage(2, clientPos.x, clientPos.y + 3 * boxH, false);
  }, pause);
  pause = drawNext(() => {
    drawPackage(1, clientPos.x, clientPos.y + 3 * boxH, false);
  }, pause);

  // Reset
  pause = drawNext(() => {}, pause + 3 * timeDiff);

  // Alert with received package
  setTimeout(function () {
    alert(result);
  }, pause);
};
