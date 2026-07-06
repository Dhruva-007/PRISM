const maplibregl = {
  Map: jest.fn(() => ({
    on: jest.fn(),
    addControl: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    getSource: jest.fn(),
    remove: jest.fn(),
  })),
  NavigationControl: jest.fn(),
};

module.exports = maplibregl;