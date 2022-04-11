import { parse, parseFile, formatters } from 'plantuml-parser';

// parse command line args
import { argv, exit } from 'process';
import * as fs from 'fs';
import * as path from 'path';

if (argv.length == 2) {
  console.log("This script turns the plantuml into a json.")
  console.log("Usage: node plantuml-parser.js plantuml-file")
  exit()
}

// read plantuml file
fs.readFile(argv[2], 'utf8', function (err, data) {
  if (err) throw err;

  // console.log(data)

  // parse PlantUML
  const result = parse(data);

  // // Format and print parse result
  // console.log(
  //   formatters.default(result)
  // );

  // write file
  const parsed_source = path.parse(argv[2])
  const destination = path.join(parsed_source.dir, parsed_source.name + ".json")

  // only write the first result
  fs.writeFile(destination, JSON.stringify(result[0], null, 2), err => {
    if (err) {
      console.error(err)
      return
    }
    //file written successfully
    console.log("File written to: " + destination)
  })
});